# TW FinReport Scraper

[中文版說明](#tw-finreport-scraper-台灣證交所財報抓取工具)

An automated tool for scraping financial reports (Annual Reports, Quarterly Reports, and Shareholder Meeting documents) from the Taiwan Stock Exchange (TWSE) Market Observation Post System.

## Features

- **Automated Scraping**: Supports automatic downloading of annual reports, quarterly reports, and shareholder meeting documents.
- **Flexible Configuration**: Specify years, quarters, and specific stock codes.
- **Rate Limit Handling**: Built-in detection and automatic retry mechanism to avoid being blocked by TWSE.
- **Playwright Driven**: Uses Playwright to simulate browser behavior for high stability.

## Installation

### 1. Install Python Package

```bash
pip install tw-finreport-scraper
```

### 2. Install Playwright Browser

```bash
playwright install chromium
```

## Usage

### Library Usage

You can reference this package directly in your Python code or refer to `example.py` in the project.

```python
from tw_finreport_scraper import run_scraper

# Directly call the core scraper function
run_scraper(
    type="all",          # "annual", "quarterly", or "all"
    year="114",         # Minguo year
    codes=["2330"],     # List of stock codes or "ALL"
    quarters=[1, 2, 3], # List of quarters
    base_path="./data"  # Output directory
)
```

### Function Arguments (`run_scraper`)

- `type`: **Scraping Type**.
    - `annual`: Annual reports and related documents (e.g., meeting minutes, top 10 shareholders).
    - `quarterly`: Quarterly financial reports (AI1).
    - `all`: Both annual and quarterly reports.
    - *Default*: `annual`
- `year`: **Minguo Year** (e.g., `114`).
- `codes`: **Stock Codes**.
    - A list of strings, e.g., `["2330", "2498"]`.
    - Use `["ALL"]` to automatically fetch all listed stocks.
- `quarters`: **Quarters** (1, 2, 3, 4).
    - Only valid when `type` is `quarterly` or `all`.
- `cooldown`: **Rate Limit Cooldown**. Base seconds to wait when rate limited. Default is 15s.
- `retries`: **Max Retries**. Maximum attempts for rate limiting or "file processing" states. Default is 10.
- `base_path`: **Output Root Directory**. The tool will create a `twse_output` folder inside this path.

## Efficiency and Design Philosophy

### 1. Execution Time Estimate
Based on current TWSE rate limits, scraping all listed stocks for a full year's data takes approximately **2 to 4 days**.

### 2. Regarding Proxy Support
This tool **does not include Proxy support** for the following reasons:
- **Low Frequency**: Financial reports are updated infrequently (4 times a year for quarterly, once for annual).
- **No Urgency**: Stability is prioritized over speed.

### 3. Environment Recommendation (No Jupyter)
**Strongly discouraged** to run this in Jupyter Notebook due to conflicts between Playwright's async mechanism and Jupyter's event loop. Please use standard Python scripts (`.py`).

---

# TW FinReport Scraper (台灣證交所財報抓取工具)

這是一個用於自動化抓取台灣證券交易所（TWSE）公開資訊觀測站中上市櫃公司財報（年報、季報、股東會文件）的工具。

## 功能特點

- **自動化抓取**：支援年報、季報及股東會相關文件的自動下載。
- **彈性設定**：可指定年份、季度以及特定的股票代碼。
- **限流處理**：內建限流偵測與自動重試機制，避免被證交所封鎖。
- **Playwright 驅動**：使用 Playwright 模擬瀏覽器行為，穩定性高。

## 安裝方式

### 1. 安裝 Python 套件

```bash
pip install tw-finreport-scraper
```

### 2. 安裝 Playwright 瀏覽器

```bash
playwright install chromium
```

## 使用方法

### 作為 Python 套件使用 (Library)

你可以在你的 Python 程式碼中直接引用此套件，或參考專案中的 `example.py`。

```python
from tw_finreport_scraper import run_scraper

# 直接呼叫套件封裝好的核心功能
run_scraper(
    type="all",          # "annual", "quarterly", 或 "all"
    year="114",         # 民國年份
    codes=["2330"],     # 股票代碼清單 或 "ALL"
    quarters=[1, 2, 3], # 季度清單
    base_path="./data"  # 輸出目錄
)
```

### 函數參數說明 (`run_scraper`)

- `type`: **抓取類型**。
    - `annual`: 僅抓取年報及股東會相關文件（如議事錄、前十大股東關係表）。
    - `quarterly`: 僅抓取財務報告（季報）。
    - `all`: 同時抓取年報與季報。
    - *預設值*: `annual`
- `year`: **指定民國年份** (例如 `114`)。
- `codes`: **指定股票代碼**。
    - 傳入字串清單，例如 `["2330", "2498"]`。
    - 傳入 `["ALL"]` 則會自動獲取全台上市櫃股票清單進行抓取。
- `quarters`: **指定季度** (1, 2, 3, 4)。
    - 僅在 `type` 為 `quarterly` 或 `all` 時有效。
- `cooldown`: **限流冷卻時間**。
    - 當偵測到限流時，程式每次休息的基礎秒數。預設為 15 秒。
- `retries`: **最大重試次數**。
    - 針對限流或檔案處理中狀態的重試次數。預設為 10 次。
- `base_path`: **指定輸出根目錄**。
    - 程式會在此目錄下建立一個 `twse_output` 資料夾。

## 執行效率與設計理念

### 1. 執行時間預估
根據目前證交所允許的請求頻率與限流機制，若要抓取**全台所有上市櫃股票**當年度的完整資料，大約需要 **2 至 4 天** 才能完成。

### 2. 關於 Proxy 功能
本工具**未內建 Proxy 功能**，主要基於以下考量：
- **低頻率需求**：財報屬於低頻率更新的資料，不具備即時競爭性。
- **無急迫性**：穩定抓取即可滿足大多數分析需求。

### 3. 環境建議 (不建議使用 Jupyter)
**強烈不建議**在 Jupyter Notebook 環境下執行此工具。
- 由於 Playwright 的非同步機制與 Jupyter 的事件迴圈經常發生衝突。
- 請使用標準的 Python 腳本 (`.py`) 在終端機執行。

## 專案結構

- `tw_finreport_scraper/`: 套件核心目錄。
  - `main.py`: 主程式邏輯。
  - `annual.py`: 處理年報抓取。
  - `quarterly.py`: 處理季報抓取。
  - `stocks.py`: 獲取股票代碼清單。
  - `common.py`: 共用工具函數。

## 免責聲明

本工具僅供學術研究與個人使用，請遵守證券交易所的使用規範。

## 授權條款

MIT License
