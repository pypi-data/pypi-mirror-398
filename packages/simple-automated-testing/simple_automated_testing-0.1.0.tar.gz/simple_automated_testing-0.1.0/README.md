# Simple Automated Testing

自動化測試框架與 CLI（MVP），支援 API 測試、OpenAPI 回應驗證、BigQuery 驗證、pipeline/waitUntil 輪詢與報告輸出。

## 功能特色

- API 測試與自訂斷言（狀態碼、JSON 欄位、文字內容等）
- OpenAPI 回應驗證（JSON body，$ref 僅支援內部參照）
- BigQuery schema 與資料內容驗證
- Pipeline 編排與 waitUntil 輪詢、預設 fail-fast
- CLI + SDK 雙介面，支援 JUnit 與人類可讀報告

## 目錄

- [需求](#需求)
- [安裝](#安裝)
- [快速開始](#快速開始)
- [設定檔](#設定檔)
- [Demo](#demo)
- [OpenAPI 回應驗證](#openapi-回應驗證)
- [CLI](#cli)
- [SDK](#sdk)
- [環境變數覆寫](#環境變數覆寫)
- [回傳碼](#回傳碼)
- [發布](#發布)
- [測試](#測試)
- [BigQuery 注意事項](#bigquery-注意事項)

## 需求

- Python 3.11
- uv（專案管理與執行）

## 安裝

一般使用（安裝至其他專案）：

```bash
pip install simple-automated-testing
```

或使用 uv：

```bash
uv pip install simple-automated-testing
```

若你的專案使用 uv 管理相依：

```bash
uv add simple-automated-testing
```

安裝後可直接使用 CLI：

```bash
simple-test --help
```

開發本專案時，在專案根目錄執行：

```bash
uv sync --extra dev
```

## 快速開始

產生設定檔並執行：

```bash
uv run simple-test init --output ./demo/simple-test.yaml
uv run simple-test run --config ./demo/simple-test.yaml
```

只執行 pipeline：

```bash
uv run simple-test run --config ./demo/simple-test.yaml --pipeline <pipelineId>
```

## 設定檔

可直接使用 `demo/simple-test.yaml`（完整範例：API/OpenAPI/BigQuery/pipeline/waitUntil/報告設定）。
Demo 使用說明：`demo/README.md`。

最小可用範例：

```yaml
projectName: sample
apiTargets:
  - id: main
    baseUrl: https://example.com
tests:
  - type: api
    name: health
    target: main
    path: /health
    assertions:
      - type: status_code
        expected: 200
```

## Demo

- 啟動測試 API 伺服器與執行指令請見 `demo/README.md`
- Demo 預設使用 `http://127.0.0.1:8000` 作為 API baseUrl

## OpenAPI 回應驗證

可提供全域 `openApiSpecPath`，也可在單一 API test 內覆寫 `openApiSpecPath`。

```yaml
openApiSpecPath: ./demo/fixtures/openapi.yaml
tests:
  - type: api
    name: health
    target: main
    path: /health
    method: GET
    assertions:
      - type: status_code
        expected: 200
      - type: openapi
    # openApiSpecPath: ./demo/fixtures/openapi.yaml
```

## CLI

- `run`：執行測試或 pipeline
- `list`：列出可執行的測試與 pipeline
- `init`：產生範例設定檔

```bash
uv run simple-test run --config ./demo/simple-test.yaml
uv run simple-test run --config ./demo/simple-test.yaml --pipeline <pipelineId>
uv run simple-test list --config ./demo/simple-test.yaml
```

## SDK

使用設定檔：

```python
from simple_automated_testing import run, render_human_summary

result = run(config_path="./demo/simple-test.yaml")
print(render_human_summary(result))
```

純程式化（不讀設定檔）：

```python
from simple_automated_testing import run_with_config

config = {
    "projectName": "sample",
    "apiTargets": [{"id": "main", "baseUrl": "https://example.com"}],
    "tests": [
        {
            "type": "api",
            "name": "health",
            "target": "main",
            "path": "/health",
            "assertions": [{"type": "status_code", "expected": 200}],
        }
    ],
}

result = run_with_config(config=config)
print(result.status)

# 需要自訂 client 時：
# result = run_with_config(config=config, api_client=MyApiClient(), bq_client=MyBigQueryClient())
```

## 環境變數覆寫

可搭配環境變數覆寫（例如 CI 提供憑證與 BigQuery 參數）：

```bash
export SIMPLE_TEST_BQ_PROJECT_ID=your-project
export SIMPLE_TEST_BQ_DATASET=your_dataset
export SIMPLE_TEST_HUMAN_REPORT_ENABLED=true
export SIMPLE_TEST_HUMAN_REPORT_OUTPUT_DIR=./report
export SIMPLE_TEST_HUMAN_REPORT_FILE_NAME=human-report.html
```

## 回傳碼

- `0`：全部通過
- `1`：有失敗
- `2`：設定檔或執行前置錯誤

## 發布

發布前請先更新 `pyproject.toml` 的 `version`。

使用 pip：

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine upload dist/*
```

使用 uv：

```bash
uv pip install --upgrade build twine
uv run python -m build
uv run python -m twine upload dist/*
```

## 測試

```bash
uv run python -m pytest
```

## BigQuery 注意事項

- 執行 BigQuery 測試前需在 `identities` 提供服務帳戶 JSON 金鑰檔路徑。
- `bigQuery.projectId` 與 `bigQuery.dataset` 必須可存取。
- 在 CI 中建議以安全方式提供金鑰檔並在設定檔引用其路徑。
