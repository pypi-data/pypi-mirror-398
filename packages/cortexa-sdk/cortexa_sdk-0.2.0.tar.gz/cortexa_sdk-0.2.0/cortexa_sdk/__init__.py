# Copyright (c) 2025 Vortek Inc. and Tuanliu (Hainan Special Economic Zone) Technology Co., Ltd.
# All rights reserved.
# 本软件版权归 Vortek Inc.（除中国大陆地区）与 湍流（海南经济特区）科技有限责任公司（中国大陆地区）所有。
# 请根据许可协议使用本软件。
import os
import json
import time
import requests
from enum import Enum
from pathlib import Path

__all__ = ["CortexaClient", "download_dataset", "ExportType"]

DEFAULT_CONFIG_PATH = Path.home() / ".cortexa" / "config.json"
DEFAULT_DATASET_DIR = Path.home() / ".cortexa" / "datasets"


class ExportType(str, Enum):
    """Export type values supported by the server."""

    JSON = "JSON"
    YOLO = "YOLO"
    COCO = "COCO"


class AnnotationType(str, Enum):
    """Annotation type values supported by the server."""

    RECT = "rect"
    POLYGON = "polygon"
    CUBOID = "cuboid"


class CortexaClient:
    """Simple client for downloading datasets.

    Configuration values are resolved in the following order:
    1. Function parameters
    2. Values from the JSON config file
    3. Environment variables

    Environment variables fall back to built-in defaults if not set.
    """

    def __init__(self, api_key=None, base_url=None, config_file=None):
        # Parameter > config > environment
        config_file = config_file or os.getenv(
            "CORTEXA_CONFIG", str(DEFAULT_CONFIG_PATH)
        )
        config_path = Path(config_file)
        config = {}
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

        self.api_key = api_key or config.get("api_key") or os.getenv("CORTEXA_API_KEY")
        self.base_url = (
            base_url or config.get("base_url") or os.getenv("CORTEXA_BASE_URL")
        )
        if not self.base_url:
            raise ValueError(
                "base_url must be provided via parameter, config file or environment variable CORTEXA_BASE_URL"
            )
        self._config = config

    def _resolve_dir(self, kind: str, override_path: str | None) -> Path:
        env_map = {
            "dataset": "CORTEXA_DATASET_DIR",
        }
        default_map = {
            "dataset": DEFAULT_DATASET_DIR,
        }
        config_key_map = {
            "dataset": "dataset_dir",
        }
        path = (
            override_path
            or self._config.get(config_key_map[kind])
            or os.getenv(env_map[kind], str(default_map[kind]))
        )
        p = Path(path).expanduser()
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _api_request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Perform an HTTP request against the Cortexa API."""
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        resp = requests.request(method, url, headers=self._headers(), **kwargs)
        resp.raise_for_status()
        return resp

    def _headers(self):
        headers = {}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        return headers

    def download_dataset(
        self,
        dataset_id: str,
        export_type: ExportType = ExportType.JSON,
        annotation_type: AnnotationType | None = None,
        download_dir: str | None = None,
        assets_included: bool = True,
        project_id: str | None = None,
        label_list: list[str] | None = None,
        filter_by_labels: bool = False,
    ) -> Path:
        """Download a dataset by creating a download task and polling for completion."""
        target_dir = self._resolve_dir("dataset", download_dir)

        if export_type == ExportType.YOLO and not annotation_type:
            raise ValueError("annotation_type must be provided for YOLO export")

        # Validate label_list
        if label_list:
            if not isinstance(label_list, list) or not all(
                isinstance(label, str) for label in label_list
            ):
                raise ValueError("label_list must be a list of strings")
            if export_type not in [ExportType.YOLO, ExportType.JSON]:
                raise ValueError(
                    "label_list is only valid for YOLO and JSON export types"
                )

        # Validate filter_by_labels
        if filter_by_labels:
            if export_type not in [ExportType.YOLO, ExportType.JSON]:
                raise ValueError(
                    "filter_by_labels is only valid for YOLO and JSON export types"
                )
            if not label_list:
                raise ValueError("filter_by_labels requires label_list to be provided")

        # Create download task
        resp = self._api_request(
            "POST",
            "dataset/download-task-create",
            json={
                "dataset_id": dataset_id,
                "export_type": export_type.value,
                "assets_included": assets_included,
                "annotation_type": annotation_type.value if annotation_type else None,
                "project_id": project_id,
                "label_list": label_list,
                "filter_by_labels": filter_by_labels,
            },
        )
        if resp.json().get("code") != 202:
            raise RuntimeError(
                f"Failed to create download task: {resp.json().get('message', 'Unknown error')}"
            )
        print(
            f"Created download task for dataset {dataset_id} with export type {export_type.value} and assets {'included' if assets_included else 'excluded'}"
        )
        task_id = resp.json()["data"]["task_id"]
        print(f"Created dataset download task {task_id} for {dataset_id}")

        zip_url = None
        last_progress = -1
        is_uploading = False
        last_status = None

        try:
            while not zip_url:
                time.sleep(2)
                poll = self._api_request(
                    "GET",
                    "task/detail",
                    params={"task_id": task_id},
                )
                data = poll.json().get("data", {})
                if not data:
                    raise RuntimeError(f"Download task polling failed: {poll.json()}")
                progress = data.get("progress", 0)
                status = data.get("status")
                if not assets_included:
                    progress = (
                        100  # If assets are not included, consider the task complete
                    )
                if progress != last_progress or status != last_status:
                    msg = (
                        f"dataset task {task_id} status: {status} progress: {progress}%"
                    )
                    # print(msg)
                    print(msg, end="\r", flush=True)
                    last_progress = progress
                    last_status = status
                if status == "FAILED":
                    raise RuntimeError(data.get("error_message", "Task failed"))
                if progress == 100 and status == "PROCESSING" and not is_uploading:
                    print(
                        "Download to backend server completed successfully, waiting for uploading to Database. If it takes too long, please check the (celery worker) server logs."
                    )
                    is_uploading = True
                zip_url = data.get("zip_url")

        except Exception as e:
            # Acknowledge the task to eliminate the frontend download notification issue
            ack = self._api_request(
                "POST",
                "task/acknowledge-download-task",
                json={"task_id": task_id},
            )
            print(f"Error occurred while polling download task: {e}")
            raise RuntimeError(
                f"Failed to create download task: {resp.json().get('message', 'Unknown error')}"
            )
        print()
        # Acknowledge the task to eliminate the frontend download notification issue
        ack = self._api_request(
            "POST",
            "task/acknowledge-download-task",
            json={"task_id": task_id},
        )
        try:
            resp = requests.get(zip_url, stream=True)
            resp.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            # print the ip and port of the file server
            print(f"Failed to connect to file server: {e}")
            print(
                f"Could not connect to the file server for dataset download at {zip_url}."
            )
            print(f"Please check if the file server is running at {self.base_url}.")
            raise RuntimeError(
                f"Could not connect to the file server for dataset download."
                f" Please check if the file server is running at {self.base_url}."
            ) from e
        except requests.exceptions.RequestException as e:
            print(f"Download failed: {e}")
            raise RuntimeError("Dataset download failed due to a network error.") from e
        out_file = target_dir / f"{dataset_id}.zip"
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        spinner = "|/-\\"
        spin_idx = 0
        spin_step = 50  # Update spinner every 50 chunks

        with open(out_file, "wb") as f:
            for chunk_idx, chunk in enumerate(resp.iter_content(chunk_size=8192)):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = int(downloaded * 100 / total)
                        if (
                            chunk_idx % spin_step == 0
                        ):  # Only update spinner every spin_step chunks
                            print(
                                f"Downloaded {pct}% {spinner[spin_idx % len(spinner)]}",
                                end="\r",
                                flush=True,
                            )
                            spin_idx += 1
        print(f"Downloaded 100%.   ")  # Move to the next line after the spinner
        print(f"Saved dataset to {out_file}")
        return out_file


def download_dataset(
    dataset_id: str,
    export_type: ExportType = ExportType.JSON,
    annotation_type: AnnotationType | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    download_dir: str | None = None,
    config_file: str | None = None,
    assets_included: bool = True,
    project_id: str | None = None,
    label_list: list[str] | None = None,
    filter_by_labels: bool = False,
) -> Path:
    client = CortexaClient(api_key=api_key, base_url=base_url, config_file=config_file)
    return client.download_dataset(
        dataset_id,
        export_type,
        annotation_type,
        download_dir,
        assets_included,
        project_id,
        label_list,
        filter_by_labels,
    )
