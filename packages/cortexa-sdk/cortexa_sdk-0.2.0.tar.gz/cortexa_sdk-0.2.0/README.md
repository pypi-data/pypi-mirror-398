
<!--
Copyright (c) 2025 Vortek Inc. and Tuanliu (Hainan Special Economic Zone) Technology Co., Ltd.
All rights reserved.
本软件版权归 Vortek Inc.（除中国大陆地区）与 湍流（海南经济特区）科技有限责任公司（中国大陆地区）所有。
请根据许可协议使用本软件。
-->

# Cortexa SDK

The Cortexa SDK is a Python client for downloading datasets from a Cortexa server, supporting both programmatic and CLI usage.

## Installation

```bash
pip install cortexa-sdk
```

## Configuration

You can configure the SDK in three ways (precedence: function parameters > config file > environment variables):

1. **Function parameters** (passed directly to `download_dataset`)
2. **Config file** (`~/.cortexa/config.json`)
3. **Environment variables**

**Example config file** (auto-generate with `cortexa-sdk --init-config`):

```json
{
  "api_key": "your-api-key",
  "base_url": "http://your-cortexa-server/api/v1",
  "dataset_dir": "~/datasets"
}
```

**Environment variables:**
- `CORTEXA_API_KEY` – API key
- `CORTEXA_BASE_URL` – Base URL of the Cortexa server
- `CORTEXA_DATASET_DIR` – Default dataset download directory
- `CORTEXA_CONFIG` – Path to a JSON config file (defaults to `~/.cortexa/config.json`)

## Usage

**Python API:**

You can use the SDK in two ways:

**1. Pass all parameters explicitly (highest precedence):**
```python
from cortexa_sdk import download_dataset, ExportType, AnnotationType

path = download_dataset(
    dataset_id="DATASET_ID",
    export_type=ExportType.JSON,
    annotation_type=AnnotationType.RECT,
    api_key="YOUR_API_KEY",
    base_url="http://your-cortexa-server/api/v1",
    download_dir="~/datasets",
    assets_included=True
)
print("Dataset saved to", path)
```

**2. Use config file or environment variables (lower precedence):**
```python
from cortexa_sdk import download_dataset, ExportType, AnnotationType

path = download_dataset("DATASET_ID", export_type=ExportType.JSON, annotation_type=AnnotationType.RECT)
print("Dataset saved to", path)
```
In this case, the SDK will read values from `~/.cortexa/config.json` or environment variables if parameters are not provided.

**CLI:**

```bash
cortexa-sdk --init-config  # Generate default config file if needed
cortexa-sdk -d "DATASET_ID" --export-type YOLO --annotation-type rect
cortexa-sdk -d "DATASET_ID" \
  --export-type JSON \
  --annotation-type rect \
  --api-key TOKEN \
  --base-url http://localhost:8000/api/v1 \
  --download-dir ./tmp/datasets \
  --assets-included True
```

**Example output:**

```
Created download task for dataset 688a26a52b1a60e8375b98d7
Created dataset download task 688a79d2b3c851acb0606df6 for 688a26a52b1a60e8375b98d7
dataset task 688a79d2b3c851acb0606df6 status: PROCESSING progress: 40%
... (progress updates) ...
dataset task 688a79d2b3c851acb0606df6 status: COMPLETED progress: 100%
Downloading dataset from ...
Saved dataset to tmp/datasets/688a26a52b1a60e8375b98d7.zip
```

## Examples

**Using environment variables:**

```bash
export CORTEXA_API_KEY="TOKEN"
export CORTEXA_BASE_URL="https://api.example.com/api/v1"
python - <<'PY'
from cortexa_sdk import download_dataset
download_dataset("dataset123")
PY
```

**Using a config file:**

```python
from cortexa_sdk import download_dataset, ExportType
path = download_dataset("dataset123", export_type=ExportType.COCO)
print(path)
```

**Overriding with parameters:**

```python
from cortexa_sdk import download_dataset, ExportType

download_dataset(
    "dataset123",
    export_type=ExportType.COCO,
    api_key="TOKEN",
    base_url="https://api.example.com/api/v1",
    download_dir="/tmp/datasets",
    assets_included=True,
)
```

## Configuration Resolution Order

1. Parameters passed to `download_dataset`
2. Values from the config file (`~/.cortexa/config.json` or as set by `CORTEXA_CONFIG`)
3. Environment variables


## Project Structure

The main files and folders for the Cortexa SDK project are organized as follows:

```
cortexa-sdk-project/
│
├── pyproject.toml                # Project metadata and build configuration
├── README.md                     # This documentation file
├── test-download.py              # Example/test script for dataset download
├── cortexa_sdk/                  # SDK source code package
│   ├── __init__.py               # SDK main logic and API
│   └── cli.py                    # Command-line interface entry point
│
└── ... (other files and folders)
```

- `pyproject.toml`: Defines the package, dependencies, and CLI entry point.
- `README.md`: Documentation for installation, configuration, usage, and development.
- `test-download.py`: Example script to demonstrate SDK usage for downloading datasets.
- `cortexa_sdk/`: The main SDK Python package.
  - `__init__.py`: Implements the SDK API (e.g., `download_dataset`).
  - `cli.py`: Implements the CLI (`cortexa-sdk` command).

You can run the CLI directly after installation:

```bash
cortexa-sdk --help
```

Or use the SDK in your own Python scripts as shown in the usage examples above.

## Releasing to PyPI

1. Install build tools:
   ```bash
   pip install --upgrade setuptools build twine
   ```
2. Build the package:
   ```bash
   python -m build
   ```
3. Upload to PyPI:
   ```bash
   twine upload dist/*
   ```
4. Tag and push the release in git:
   ```bash
   git tag v<version>
   git push --tags
   ```
5. (Optional) Test uploads using [TestPyPI](https://test.pypi.org/) with `twine`.

**Rebuild and reinstall locally:**
```bash
python -m build
pip install dist/cortexa_sdk-*.whl --force-reinstall
```