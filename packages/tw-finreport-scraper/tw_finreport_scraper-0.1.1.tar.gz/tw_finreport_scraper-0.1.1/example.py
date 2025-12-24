from tw_finreport_scraper import run_scraper

# --- 爬蟲設定參數 ---
# 指定要抓取的民國年份 (例如: "114")
TARGET_YEAR = "114"

# 指定股票代碼清單。
# - 若要抓取所有股票，請設為 ["ALL"]
# - 若要指定特定股票，請列出代碼，例如 ["2330", "2498"]
STOCK_CODES = ["2330"]

# 指定要抓取的季度清單 (僅在 type 為 quarterly 或 all 時有效)
# 選項: [1, 2, 3, 4]
TARGET_QUARTERS = [1, 2, 3]

# 預設抓取類型
# 選項: 
# - "annual": 僅抓取年報及股東會相關文件 
# - "quarterly": 僅抓取季報 (AI1)
# - "all": 同時抓取年報與季報
DEFAULT_TYPE = "all"

# 每次請求之間的隨機等待時間範圍 (秒)，避免被偵測為機器人
SLEEP_RANGE = (10.0, 15.0)

# 當觸發限流 (查詢過量) 或檔案處理中時，每次休息的基礎秒數
COOL_DOWN_BASE = 15

# 最大重試次數 (針對限流或檔案處理中的等待次數)
MAX_RETRIES = 10
# ------------------

if __name__ == "__main__":
    # 直接呼叫套件封裝好的核心功能
    run_scraper(
        type=DEFAULT_TYPE,
        year=TARGET_YEAR,
        codes=STOCK_CODES,
        quarters=TARGET_QUARTERS,
        cooldown=COOL_DOWN_BASE,
        retries=MAX_RETRIES,
        sleep_range=SLEEP_RANGE,
        base_path="./data"  # 輸出根目錄
    )
