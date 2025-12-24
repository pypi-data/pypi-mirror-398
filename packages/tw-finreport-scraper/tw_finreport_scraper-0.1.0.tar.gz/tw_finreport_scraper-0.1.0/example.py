import argparse
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

def main():
    # 設定命令列參數，預設值從上方設定讀取
    parser = argparse.ArgumentParser(description="證交所報表抓取工具")
    parser.add_argument("--type", type=str, choices=["annual", "quarterly", "all"], 
                        default=DEFAULT_TYPE, 
                        help=f"抓取類型 (預設: {DEFAULT_TYPE})")
    parser.add_argument("--year", type=str, default=TARGET_YEAR, 
                        help=f"指定年份 (預設: {TARGET_YEAR})")
    parser.add_argument("--codes", nargs="+", default=STOCK_CODES, 
                        help=f"指定股票代碼 (預設: {' '.join(STOCK_CODES)})")
    parser.add_argument("--quarters", nargs="+", type=int, default=TARGET_QUARTERS, 
                        help=f"指定季度 (預設: {TARGET_QUARTERS})")
    parser.add_argument("--cooldown", type=int, default=COOL_DOWN_BASE,
                        help=f"限流冷卻時間 (預設: {COOL_DOWN_BASE})")
    parser.add_argument("--retries", type=int, default=MAX_RETRIES,
                        help=f"最大重試次數 (預設: {MAX_RETRIES})")
    
    args = parser.parse_args()
    
    # 直接呼叫套件封裝好的核心功能
    run_scraper(
        type=args.type,
        year=args.year,
        codes=args.codes,
        quarters=args.quarters,
        cooldown=args.cooldown,
        retries=args.retries,
        sleep_range=SLEEP_RANGE
    )

if __name__ == "__main__":
    main()
