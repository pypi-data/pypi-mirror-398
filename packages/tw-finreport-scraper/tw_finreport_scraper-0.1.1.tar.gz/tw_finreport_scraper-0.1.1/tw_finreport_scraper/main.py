import json
import time
import random
from pathlib import Path
from playwright.sync_api import sync_playwright

# 匯入自定義模組
from .annual import crawl_all_annual_reports, DOC_TYPES
from .quarterly import crawl_quarterly_report
from .stocks import fetch_all_stock_codes

# --- 預設爬蟲設定參數 ---
TARGET_YEAR = "114"
STOCK_CODES = ["ALL"]
TARGET_QUARTERS = [1, 2, 3]
DEFAULT_TYPE = "annual"
SLEEP_RANGE = (10.0, 15.0)
COOL_DOWN_BASE = 15
MAX_RETRIES = 10

def run_scraper(
    type=DEFAULT_TYPE,
    year=TARGET_YEAR,
    codes=STOCK_CODES,
    quarters=TARGET_QUARTERS,
    cooldown=COOL_DOWN_BASE,
    retries=MAX_RETRIES,
    sleep_range=SLEEP_RANGE,
    base_path=None
):
    """
    執行爬蟲的核心功能函數。
    """
    # 增加一層資料夾，預設名稱為 "twse_output"
    if base_path is None:
        root_path = Path.cwd() / "twse_output"
    else:
        root_path = Path(base_path) / "twse_output"
    
    root_path.mkdir(parents=True, exist_ok=True)

    # 處理 "ALL" 股票代碼
    final_codes = codes
    if isinstance(codes, list) and "ALL" in [c.upper() for c in codes if isinstance(c, str)]:
        final_codes = fetch_all_stock_codes()
    elif isinstance(codes, str) and codes.upper() == "ALL":
        final_codes = fetch_all_stock_codes()
    
    failed_tasks = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for code in final_codes:
            print(f"\n=== 開始處理股票: {code} ===")
            
            # 1. 抓取年報及股東會文件
            if type in ["annual", "all"]:
                print(f"--- 執行年報及股東會文件抓取 ({year}年) ---")
                time.sleep(random.uniform(*sleep_range))
                # 傳入 root_path，annual.py 會在下面建立各類別資料夾
                failed_list = crawl_all_annual_reports(page, year, code, root_path, cooldown, retries)
                for f_dtype in failed_list:
                    failed_tasks.append({"code": code, "type": "annual", "dtype": f_dtype, "year": year})
            
            if type == "all":
                time.sleep(random.uniform(*sleep_range))

            # 2. 抓取季報
            if type in ["quarterly", "all"]:
                print(f"--- 執行季報抓取 ({year}年 Q{quarters}) ---")
                save_dir_q = root_path / "財務報告(季報)"
                save_dir_q.mkdir(parents=True, exist_ok=True)
                for q in quarters:
                    time.sleep(random.uniform(*sleep_range))
                    success = crawl_quarterly_report(page, year, q, code, save_dir_q, cooldown, retries)
                    if not success:
                        failed_tasks.append({"code": code, "type": "quarterly", "quarter": q, "year": year})

        browser.close()

    # 儲存失敗清單
    if failed_tasks:
        fail_file = root_path / "failed_tasks.json"
        with open(fail_file, "w", encoding="utf-8") as f:
            json.dump(failed_tasks, f, ensure_ascii=False, indent=2)
        print(f"\n⚠️ 抓取完成，共有 {len(failed_tasks)} 個任務失敗，清單已存至 {fail_file}")
    else:
        print("\n✅ 所有任務抓取成功！")
    
    return failed_tasks
