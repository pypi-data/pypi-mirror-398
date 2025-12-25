# Copyright (c) 2025 Vortek Inc. and Tuanliu (Hainan Special Economic Zone) Technology Co., Ltd.
# All rights reserved.
# 本软件版权归 Vortek Inc.（除中国大陆地区）与 湍流（海南经济特区）科技有限责任公司（中国大陆地区）所有。
# 请根据许可协议使用本软件。
"""Pytest tests for cortexa_sdk that can run without celery startup."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import requests

from cortexa_sdk import (
    CortexaClient,
    download_dataset,
    ExportType,
    AnnotationType,
)


class TestCortexaClient:
    """Tests for CortexaClient class."""

    def test_init_with_base_url(self):
        """Test client initialization with base_url."""
        client = CortexaClient(base_url="http://test.com/api/v1")
        assert client.base_url == "http://test.com/api/v1"

    def test_init_without_base_url_raises(self):
        """Test that initialization without base_url raises ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=False):
                with pytest.raises(ValueError, match="base_url must be provided"):
                    CortexaClient()

    def test_init_with_api_key(self):
        """Test client initialization with api_key."""
        client = CortexaClient(base_url="http://test.com/api/v1", api_key="test-key")
        assert client.api_key == "test-key"

    def test_headers_with_api_key(self):
        """Test that headers include API key when provided."""
        client = CortexaClient(base_url="http://test.com/api/v1", api_key="test-key")
        headers = client._headers()
        assert headers["X-API-KEY"] == "test-key"

    def test_headers_without_api_key(self):
        """Test that headers are empty when no API key."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=False):
                client = CortexaClient(base_url="http://test.com/api/v1")
                headers = client._headers()
                assert headers == {}


class TestDownloadDatasetValidation:
    """Tests for download_dataset validation logic."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return CortexaClient(base_url="http://test.com/api/v1", api_key="test-key")

    @pytest.fixture
    def mock_api_request(self):
        """Mock the _api_request method."""
        with patch.object(
            CortexaClient,
            "_api_request",
            return_value=Mock(
                json=lambda: {"code": 202, "data": {"task_id": "test-task"}}
            ),
        ) as mock:
            yield mock

    @pytest.fixture
    def mock_polling_and_download(self):
        """Mock polling and download to avoid actual HTTP calls."""
        with patch.object(CortexaClient, "_api_request") as mock_request:
            # Mock create task response
            create_resp = Mock()
            create_resp.json.return_value = {
                "code": 202,
                "data": {"task_id": "test-task"},
            }
            # Mock polling response
            poll_resp = Mock()
            poll_resp.json.return_value = {
                "data": {
                    "progress": 100,
                    "status": "COMPLETED",
                    "zip_url": "http://test.com/file.zip",
                }
            }
            # Mock acknowledge response
            ack_resp = Mock()
            ack_resp.json.return_value = {"code": 200}
            # Mock download response
            download_resp = Mock()
            download_resp.headers = {"Content-Length": "1000"}
            download_resp.iter_content.return_value = [b"test" * 100]
            download_resp.raise_for_status = Mock()

            def side_effect(method, path, **kwargs):
                if method == "POST" and "download-task-create" in path:
                    return create_resp
                elif method == "GET" and "task/detail" in path:
                    return poll_resp
                elif method == "POST" and "acknowledge" in path:
                    return ack_resp
                return Mock()

            mock_request.side_effect = side_effect

            with patch("requests.get", return_value=download_resp):
                with patch("time.sleep"):  # Speed up tests
                    yield mock_request

    def test_yolo_requires_annotation_type(self, client, mock_polling_and_download):
        """Test that YOLO export requires annotation_type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(
                ValueError, match="annotation_type must be provided for YOLO"
            ):
                client.download_dataset(
                    dataset_id="test-dataset",
                    export_type=ExportType.YOLO,
                    download_dir=tmpdir,
                )

    def test_label_list_must_be_list_of_strings(self, client):
        """Test that label_list must be a list of strings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(
                ValueError, match="label_list must be a list of strings"
            ):
                client.download_dataset(
                    dataset_id="test-dataset",
                    export_type=ExportType.JSON,
                    label_list=["label1", 123],  # Invalid: contains non-string
                    download_dir=tmpdir,
                )

    def test_label_list_must_be_list_not_string(self, client):
        """Test that label_list cannot be a string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(
                ValueError, match="label_list must be a list of strings"
            ):
                client.download_dataset(
                    dataset_id="test-dataset",
                    export_type=ExportType.JSON,
                    label_list="label1",  # Invalid: string instead of list
                    download_dir=tmpdir,
                )

    def test_label_list_can_be_none(self, client, mock_polling_and_download):
        """Test that label_list can be None without raising error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = client.download_dataset(
                dataset_id="test-dataset",
                export_type=ExportType.JSON,
                label_list=None,
                download_dir=tmpdir,
            )
            assert result.exists()

    def test_label_list_can_be_empty_list(self, client, mock_polling_and_download):
        """Test that empty label_list is handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = client.download_dataset(
                dataset_id="test-dataset",
                export_type=ExportType.JSON,
                label_list=[],
                download_dir=tmpdir,
            )
            assert result.exists()

    def test_label_list_only_valid_for_yolo_and_json(self, client):
        """Test that label_list is only valid for YOLO and JSON export types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(
                ValueError, match="label_list is only valid for YOLO and JSON"
            ):
                client.download_dataset(
                    dataset_id="test-dataset",
                    export_type=ExportType.COCO,
                    label_list=["label1"],
                    download_dir=tmpdir,
                )

    def test_filter_by_labels_only_valid_for_yolo_and_json(self, client):
        """Test that filter_by_labels is only valid for YOLO and JSON export types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(
                ValueError, match="filter_by_labels is only valid for YOLO and JSON"
            ):
                client.download_dataset(
                    dataset_id="test-dataset",
                    export_type=ExportType.COCO,
                    filter_by_labels=True,
                    download_dir=tmpdir,
                )

    def test_filter_by_labels_requires_label_list(self, client):
        """Test that filter_by_labels requires label_list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(
                ValueError, match="filter_by_labels requires label_list"
            ):
                client.download_dataset(
                    dataset_id="test-dataset",
                    export_type=ExportType.JSON,
                    filter_by_labels=True,
                    download_dir=tmpdir,
                )

    def test_valid_label_list_with_json(self, client, mock_polling_and_download):
        """Test that valid label_list works with JSON export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = client.download_dataset(
                dataset_id="test-dataset",
                export_type=ExportType.JSON,
                label_list=["label1", "label2"],
                download_dir=tmpdir,
            )
            assert result.exists()

    def test_valid_label_list_with_yolo(self, client, mock_polling_and_download):
        """Test that valid label_list works with YOLO export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = client.download_dataset(
                dataset_id="test-dataset",
                export_type=ExportType.YOLO,
                annotation_type=AnnotationType.RECT,
                label_list=["label1", "label2"],
                download_dir=tmpdir,
            )
            assert result.exists()

    def test_valid_filter_by_labels_with_json(self, client, mock_polling_and_download):
        """Test that valid filter_by_labels works with JSON export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = client.download_dataset(
                dataset_id="test-dataset",
                export_type=ExportType.JSON,
                label_list=["label1"],
                filter_by_labels=True,
                download_dir=tmpdir,
            )
            assert result.exists()


class TestDownloadDatasetAPIParameters:
    """Tests for API parameter passing in download_dataset."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return CortexaClient(base_url="http://test.com/api/v1", api_key="test-key")

    def test_api_request_includes_project_id(self, client):
        """Test that project_id is included in API request."""
        captured_json = {}

        def capture_create_request(method, path, **kwargs):
            if method == "POST" and "download-task-create" in path:
                captured_json.update(kwargs.get("json", {}))
                create_resp = Mock()
                create_resp.json.return_value = {
                    "code": 202,
                    "data": {"task_id": "test-task"},
                }
                return create_resp
            elif method == "GET" and "task/detail" in path:
                poll_resp = Mock()
                poll_resp.json.return_value = {
                    "data": {
                        "progress": 100,
                        "status": "COMPLETED",
                        "zip_url": "http://test.com/file.zip",
                    }
                }
                return poll_resp
            elif method == "POST" and "acknowledge" in path:
                ack_resp = Mock()
                ack_resp.json.return_value = {"code": 200}
                return ack_resp
            return Mock()

        with patch.object(
            CortexaClient, "_api_request", side_effect=capture_create_request
        ):
            download_resp = Mock()
            download_resp.headers = {"Content-Length": "1000"}
            download_resp.iter_content.return_value = [b"test" * 100]
            download_resp.raise_for_status = Mock()

            with patch("requests.get", return_value=download_resp):
                with patch("time.sleep"):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        client.download_dataset(
                            dataset_id="test-dataset",
                            project_id="test-project",
                            download_dir=tmpdir,
                        )

            # Check that project_id was included in the request
            assert captured_json.get("project_id") == "test-project"

    def test_api_request_includes_label_list(self, client):
        """Test that label_list is included in API request."""
        captured_json = {}

        def capture_create_request(method, path, **kwargs):
            if method == "POST" and "download-task-create" in path:
                captured_json.update(kwargs.get("json", {}))
                create_resp = Mock()
                create_resp.json.return_value = {
                    "code": 202,
                    "data": {"task_id": "test-task"},
                }
                return create_resp
            elif method == "GET" and "task/detail" in path:
                poll_resp = Mock()
                poll_resp.json.return_value = {
                    "data": {
                        "progress": 100,
                        "status": "COMPLETED",
                        "zip_url": "http://test.com/file.zip",
                    }
                }
                return poll_resp
            elif method == "POST" and "acknowledge" in path:
                ack_resp = Mock()
                ack_resp.json.return_value = {"code": 200}
                return ack_resp
            return Mock()

        with patch.object(
            CortexaClient, "_api_request", side_effect=capture_create_request
        ):
            download_resp = Mock()
            download_resp.headers = {"Content-Length": "1000"}
            download_resp.iter_content.return_value = [b"test" * 100]
            download_resp.raise_for_status = Mock()

            with patch("requests.get", return_value=download_resp):
                with patch("time.sleep"):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        client.download_dataset(
                            dataset_id="test-dataset",
                            export_type=ExportType.JSON,
                            label_list=["label1", "label2"],
                            download_dir=tmpdir,
                        )

            # Check that label_list was included in the request
            assert captured_json.get("label_list") == ["label1", "label2"]

    def test_api_request_includes_filter_by_labels(self, client):
        """Test that filter_by_labels is included in API request."""
        captured_json = {}

        def capture_create_request(method, path, **kwargs):
            if method == "POST" and "download-task-create" in path:
                captured_json.update(kwargs.get("json", {}))
                create_resp = Mock()
                create_resp.json.return_value = {
                    "code": 202,
                    "data": {"task_id": "test-task"},
                }
                return create_resp
            elif method == "GET" and "task/detail" in path:
                poll_resp = Mock()
                poll_resp.json.return_value = {
                    "data": {
                        "progress": 100,
                        "status": "COMPLETED",
                        "zip_url": "http://test.com/file.zip",
                    }
                }
                return poll_resp
            elif method == "POST" and "acknowledge" in path:
                ack_resp = Mock()
                ack_resp.json.return_value = {"code": 200}
                return ack_resp
            return Mock()

        with patch.object(
            CortexaClient, "_api_request", side_effect=capture_create_request
        ):
            download_resp = Mock()
            download_resp.headers = {"Content-Length": "1000"}
            download_resp.iter_content.return_value = [b"test" * 100]
            download_resp.raise_for_status = Mock()

            with patch("requests.get", return_value=download_resp):
                with patch("time.sleep"):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        client.download_dataset(
                            dataset_id="test-dataset",
                            export_type=ExportType.JSON,
                            label_list=["label1"],
                            filter_by_labels=True,
                            download_dir=tmpdir,
                        )

            # Check that filter_by_labels was included in the request
            assert captured_json.get("filter_by_labels") is True

    def test_api_request_all_new_parameters(self, client):
        """Test that all new parameters are included in API request."""
        captured_json = {}

        def capture_create_request(method, path, **kwargs):
            if method == "POST" and "download-task-create" in path:
                captured_json.update(kwargs.get("json", {}))
                create_resp = Mock()
                create_resp.json.return_value = {
                    "code": 202,
                    "data": {"task_id": "test-task"},
                }
                return create_resp
            elif method == "GET" and "task/detail" in path:
                poll_resp = Mock()
                poll_resp.json.return_value = {
                    "data": {
                        "progress": 100,
                        "status": "COMPLETED",
                        "zip_url": "http://test.com/file.zip",
                    }
                }
                return poll_resp
            elif method == "POST" and "acknowledge" in path:
                ack_resp = Mock()
                ack_resp.json.return_value = {"code": 200}
                return ack_resp
            return Mock()

        with patch.object(
            CortexaClient, "_api_request", side_effect=capture_create_request
        ):
            download_resp = Mock()
            download_resp.headers = {"Content-Length": "1000"}
            download_resp.iter_content.return_value = [b"test" * 100]
            download_resp.raise_for_status = Mock()

            with patch("requests.get", return_value=download_resp):
                with patch("time.sleep"):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        client.download_dataset(
                            dataset_id="test-dataset",
                            export_type=ExportType.JSON,
                            project_id="test-project",
                            label_list=["label1", "label2"],
                            filter_by_labels=True,
                            download_dir=tmpdir,
                        )

            # Check that all parameters were included
            assert captured_json.get("project_id") == "test-project"
            assert captured_json.get("label_list") == ["label1", "label2"]
            assert captured_json.get("filter_by_labels") is True

    def test_api_request_with_none_values(self, client):
        """Test that None values are properly handled in API request."""
        captured_json = {}

        def capture_create_request(method, path, **kwargs):
            if method == "POST" and "download-task-create" in path:
                captured_json.update(kwargs.get("json", {}))
                create_resp = Mock()
                create_resp.json.return_value = {
                    "code": 202,
                    "data": {"task_id": "test-task"},
                }
                return create_resp
            elif method == "GET" and "task/detail" in path:
                poll_resp = Mock()
                poll_resp.json.return_value = {
                    "data": {
                        "progress": 100,
                        "status": "COMPLETED",
                        "zip_url": "http://test.com/file.zip",
                    }
                }
                return poll_resp
            elif method == "POST" and "acknowledge" in path:
                ack_resp = Mock()
                ack_resp.json.return_value = {"code": 200}
                return ack_resp
            return Mock()

        with patch.object(
            CortexaClient, "_api_request", side_effect=capture_create_request
        ):
            download_resp = Mock()
            download_resp.headers = {"Content-Length": "1000"}
            download_resp.iter_content.return_value = [b"test" * 100]
            download_resp.raise_for_status = Mock()

            with patch("requests.get", return_value=download_resp):
                with patch("time.sleep"):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        client.download_dataset(
                            dataset_id="test-dataset",
                            project_id=None,
                            label_list=None,
                            filter_by_labels=False,
                            download_dir=tmpdir,
                        )

            # Check that None values are included in the request
            assert captured_json.get("project_id") is None
            assert captured_json.get("label_list") is None
            assert captured_json.get("filter_by_labels") is False


class TestStandaloneDownloadDataset:
    """Tests for the standalone download_dataset function."""

    def test_standalone_function_passes_parameters(self):
        """Test that standalone function passes all parameters correctly."""
        with patch.object(CortexaClient, "download_dataset") as mock_download:
            mock_download.return_value = Path("/tmp/test.zip")
            with tempfile.TemporaryDirectory() as tmpdir:
                result = download_dataset(
                    dataset_id="test-dataset",
                    export_type=ExportType.JSON,
                    base_url="http://test.com/api/v1",
                    api_key="test-key",
                    project_id="test-project",
                    label_list=["label1"],
                    filter_by_labels=True,
                    download_dir=tmpdir,
                )

            mock_download.assert_called_once()
            # The function passes arguments positionally: (dataset_id, export_type, annotation_type, download_dir, assets_included, project_id, label_list, filter_by_labels)
            call_args = mock_download.call_args
            pos_args = call_args[0]
            assert pos_args[0] == "test-dataset"  # dataset_id
            assert pos_args[1] == ExportType.JSON  # export_type
            assert pos_args[2] is None  # annotation_type
            assert pos_args[4] == True  # assets_included
            assert pos_args[5] == "test-project"  # project_id
            assert pos_args[6] == ["label1"]  # label_list
            assert pos_args[7] == True  # filter_by_labels


class TestCLI:
    """Tests for CLI interface."""

    def test_cli_with_project_id(self):
        """Test CLI with --project-id argument."""
        from cortexa_sdk.cli import main
        import sys

        with patch("cortexa_sdk.cli.download_dataset") as mock_download:
            mock_download.return_value = Path("/tmp/test.zip")
            with patch.object(
                sys,
                "argv",
                [
                    "cortexa-sdk",
                    "-d",
                    "test-dataset",
                    "--project-id",
                    "test-project",
                    "--base-url",
                    "http://test.com/api/v1",
                ],
            ):
                main()

            mock_download.assert_called_once()
            # Check keyword arguments
            call_kwargs = mock_download.call_args[1]
            assert call_kwargs.get("project_id") == "test-project"

    def test_cli_with_label_list_space_separated(self):
        """Test CLI with --label-list as space-separated values."""
        from cortexa_sdk.cli import main
        import sys

        with patch("cortexa_sdk.cli.download_dataset") as mock_download:
            mock_download.return_value = Path("/tmp/test.zip")
            with patch.object(
                sys,
                "argv",
                [
                    "cortexa-sdk",
                    "-d",
                    "test-dataset",
                    "--label-list",
                    "label1",
                    "label2",
                    "--base-url",
                    "http://test.com/api/v1",
                ],
            ):
                main()

            mock_download.assert_called_once()
            call_kwargs = mock_download.call_args[1]
            assert call_kwargs.get("label_list") == ["label1", "label2"]

    def test_cli_with_label_list_comma_separated(self):
        """Test CLI with --label-list as comma-separated values."""
        from cortexa_sdk.cli import main
        import sys

        with patch("cortexa_sdk.cli.download_dataset") as mock_download:
            mock_download.return_value = Path("/tmp/test.zip")
            with patch.object(
                sys,
                "argv",
                [
                    "cortexa-sdk",
                    "-d",
                    "test-dataset",
                    "--label-list",
                    "label1,label2,label3",
                    "--base-url",
                    "http://test.com/api/v1",
                ],
            ):
                main()

            mock_download.assert_called_once()
            call_kwargs = mock_download.call_args[1]
            assert call_kwargs.get("label_list") == [
                "label1",
                "label2",
                "label3",
            ]

    def test_cli_with_filter_by_labels(self):
        """Test CLI with --filter-by-labels flag."""
        from cortexa_sdk.cli import main
        import sys

        with patch("cortexa_sdk.cli.download_dataset") as mock_download:
            mock_download.return_value = Path("/tmp/test.zip")
            with patch.object(
                sys,
                "argv",
                [
                    "cortexa-sdk",
                    "-d",
                    "test-dataset",
                    "--label-list",
                    "label1",
                    "--filter-by-labels",
                    "--base-url",
                    "http://test.com/api/v1",
                ],
            ):
                main()

            mock_download.assert_called_once()
            call_kwargs = mock_download.call_args[1]
            assert call_kwargs.get("filter_by_labels") is True
            assert call_kwargs.get("label_list") == ["label1"]

    def test_cli_all_new_parameters(self):
        """Test CLI with all new parameters."""
        from cortexa_sdk.cli import main
        import sys

        with patch("cortexa_sdk.cli.download_dataset") as mock_download:
            mock_download.return_value = Path("/tmp/test.zip")
            with patch.object(
                sys,
                "argv",
                [
                    "cortexa-sdk",
                    "-d",
                    "test-dataset",
                    "--project-id",
                    "test-project",
                    "--label-list",
                    "label1",
                    "label2",
                    "--filter-by-labels",
                    "--base-url",
                    "http://test.com/api/v1",
                ],
            ):
                main()

            mock_download.assert_called_once()
            call_kwargs = mock_download.call_args[1]
            assert call_kwargs.get("project_id") == "test-project"
            assert call_kwargs.get("label_list") == ["label1", "label2"]
            assert call_kwargs.get("filter_by_labels") is True
