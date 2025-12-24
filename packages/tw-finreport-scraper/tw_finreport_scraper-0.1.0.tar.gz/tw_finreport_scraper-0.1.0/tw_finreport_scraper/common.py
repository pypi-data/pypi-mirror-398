import time
import random
import requests
from pathlib import Path
from pathlib import Path
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://doc.twse.com.tw/server-java/t57sb01"

def wait_for_rate_limit(page: Page, code: str, cool_down_base: int = 30, max_retries: int = 10):
    """檢查並處理證交所限流"""
    retry_count = 0
    while True:
        try:
            text = page.locator("body").inner_text()
            if "查詢過量" in text or "查詢過於頻繁" in text or "服務器忙碌" in text:
                wait_time = cool_down_base
                print(f"⚠️ 股票 {code} 觸發限流，休息 {wait_time} 秒後重試 ({retry_count}/{max_retries})...")
                time.sleep(wait_time)
                
                # 嘗試重新整理頁面
                page.reload(wait_until="domcontentloaded")
                retry_count += 1
                if retry_count > max_retries:
                    print(f"❌ 股票 {code} 達到最大重試次數，跳過。")
                    return False
                continue
            return True
        except Exception as e:
            print(f"檢查限流時發生錯誤: {e}")
            return False

def get_pdf_from_popup(pdf_page, code, cool_down_base=30, max_retries=10):
    """從彈出視窗中提取 PDF 連結並下載"""
    try:
        # 先等待頁面載入完成
        pdf_page.wait_for_load_state("domcontentloaded", timeout=30000)
        
        # 檢查彈窗是否也遇到了限流
        if not wait_for_rate_limit(pdf_page, f"{code}(彈窗)", cool_down_base, max_retries):
            pdf_page.close()
            return None

        # 增加等待時間，並處理「檔案處理中」的情況
        # 縮短單次彈窗的原地等待次數，改為更頻繁地「關掉重開」
        # 這裡固定只等 2 次，不行就回報失敗讓外層重新點擊
        max_inner_retries = 2
        for i in range(max_inner_retries): 
            try:
                # 嘗試尋找任何包含 .pdf 的連結
                pdf_page.wait_for_selector("a", timeout=cool_down_base * 1000)
                if pdf_page.locator("a[href*='.pdf']").count() > 0:
                    break
            except:
                pass
            
            text = pdf_page.locator("body").inner_text()
            if "處理中" in text or "請稍候" in text or "查詢過量" in text:
                print(f"檔案處理中或限流，原地再等 {cool_down_base} 秒... ({i+1}/{max_inner_retries})")
                time.sleep(cool_down_base)
                continue
            else:
                if pdf_page.locator("a").count() > 0:
                    break
                break # 內容異常直接跳出
        
        final_pdf_locator = pdf_page.locator("a[href*='.pdf']").first
        
        final_pdf_locator = pdf_page.locator("a[href*='.pdf']").first
        if not final_pdf_locator.count():
            final_pdf_locator = pdf_page.locator("a:has-text('.pdf')").first
        if not final_pdf_locator.count():
            final_pdf_locator = pdf_page.locator("a").first

        if not final_pdf_locator.count():
            pdf_page.close()
            return None
            
        pdf_url = final_pdf_locator.get_attribute("href")
        if pdf_url.startswith("/"):
            pdf_url = "https://doc.twse.com.tw" + pdf_url
        elif not pdf_url.startswith("http"):
            pdf_url = "https://doc.twse.com.tw/server-java/" + pdf_url
            
        response = requests.get(pdf_url, timeout=60)
        response.raise_for_status()
        pdf_page.close()
        return response.content
    except Exception as e:
        print(f"彈窗處理失敗 ({code}): {e}")
        try:
            pdf_page.close()
        except:
            pass
        return None
