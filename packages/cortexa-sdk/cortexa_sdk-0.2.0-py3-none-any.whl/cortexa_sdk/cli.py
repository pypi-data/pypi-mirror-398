# Copyright (c) 2025 Vortek Inc. and Tuanliu (Hainan Special Economic Zone) Technology Co., Ltd.
# All rights reserved.
# 本软件版权归 Vortek Inc.（除中国大陆地区）与 湍流（海南经济特区）科技有限责任公司（中国大陆地区）所有。
# 请根据许可协议使用本软件。
import argparse
from cortexa_sdk import download_dataset, ExportType, AnnotationType


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Download a dataset from Cortexa.\n\n"
            "Configuration options (priority order):\n"
            "  1. Function parameters (CLI arguments)\n"
            "  2. Config file at ~/.cortexa/config.json\n"
            "  3. Environment variables\n\n"
            "Example config file:\n"
            "  {\n"
            "    'api_key': 'your-api-key',\n"
            "    'base_url': 'http://your-cortexa-server/api/v1',\n"
            "    'dataset_dir': '~/datasets'\n"
            "  }\n\n"
            "Environment variables:\n"
            "  CORTEXA_API_KEY\n"
            "  CORTEXA_BASE_URL\n"
            "  CORTEXA_DATASET_DIR\n"
            "You can also initialize the config file with --init-config.\n"
            'example: cortexa-sdk -d "dataset-id" --export-type COCO --assets-included True --api-key your-api-key --base-url http://localhost:8000/api/v1 --download-dir ./tmp/datasets\n'
            "after setup the config.json or environment variables, use\n"
            ' cortexa-sdk -d "dataset-id" --export-type "ExportType"'
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("-d", "--dataset-id", help="Dataset ID to download")
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Initialize ~/.cortexa/config.json with default values",
    )
    parser.add_argument(
        "-t",
        "--export-type",
        default="JSON",
        choices=["COCO", "YOLO", "JSON"],
        help="Export type",
    )
    parser.add_argument(
        "--annotation-type",
        choices=["rect", "polygon", "cuboid"],
        help="Annotation type",
    )
    parser.add_argument(
        "--assets-included",
        default=True,
        action="store_true",
        help="Include assets in the download",
    )
    parser.add_argument("--api-key", help="API key")
    parser.add_argument(
        "--base-url",
        help="Base URL of the server, such as http://localhost:8000/api/v1",
    )
    parser.add_argument(
        "--download-dir", default="./tmp/datasets", help="Download directory"
    )
    parser.add_argument(
        "--project-id",
        help="Project ID (optional)",
    )
    parser.add_argument(
        "--label-list",
        nargs="*",
        help="List of label names to filter by (optional, only valid for YOLO and JSON export types). Can be provided as space-separated values or comma-separated.",
    )
    parser.add_argument(
        "--filter-by-labels",
        action="store_true",
        help="Filter dataset by labels (only valid for YOLO and JSON export types, requires --label-list)",
    )
    args = parser.parse_args()

    if args.init_config:
        from pathlib import Path
        import json

        config_dir = Path.home() / ".cortexa"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "config.json"
        default_config = {
            "api_key": "your-api-key",
            "base_url": "http://your-cortexa-server/api/v1",
            "dataset_dir": str(config_dir / "datasets"),
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)
        print(f"Initialized config file at {config_path}")
        return

    if not args.dataset_id:
        parser.error(
            "the following arguments are required: -d/--dataset-id (unless --init-config is used)"
        )

    # Parse label_list: handle comma-separated values if provided as a single string
    label_list = None
    if args.label_list:
        # Flatten any comma-separated values
        label_list = []
        for item in args.label_list:
            # Split by comma and strip whitespace
            label_list.extend(
                [label.strip() for label in item.split(",") if label.strip()]
            )

    path = download_dataset(
        dataset_id=args.dataset_id,
        export_type=ExportType(args.export_type),
        api_key=args.api_key,
        base_url=args.base_url,
        download_dir=args.download_dir,
        assets_included=args.assets_included,
        annotation_type=(
            AnnotationType(args.annotation_type) if args.annotation_type else None
        ),
        project_id=args.project_id,
        label_list=label_list,
        filter_by_labels=args.filter_by_labels,
    )
    print("Downloaded to:", path)


if __name__ == "__main__":
    main()
