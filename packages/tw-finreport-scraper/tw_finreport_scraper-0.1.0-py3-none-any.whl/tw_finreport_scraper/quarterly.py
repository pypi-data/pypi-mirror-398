from pathlib import Path
from .common import BASE_URL, wait_for_rate_limit

def crawl_quarterly_report(page, year, quarter, code, save_dir, cool_down_base=30, max_retries=10):
    """抓取季報文件"""
    url = f"{BASE_URL}?step=1&colorchg=1&co_id={code}&year={year}&seamon=&mtype=A&dtype=AI1&"
    page.goto(url, wait_until="domcontentloaded")
    
    if not wait_for_rate_limit(page, code, cool_down_base, max_retries):
        return False

    # 季報檔名格式: {西元年}{兩位季度}_{symbol}_AI1.pdf
    ad_year = int(year) + 1911
    format_q = f"{quarter:02d}"
    pdf_name_key = f"{ad_year}{format_q}_{code}_AI1.pdf"
    
    selector = f"//a[contains(@href, 'javascript:readfile2') and contains(@href, '{pdf_name_key}')]"
    link_element = page.locator(selector).first
    
    if not link_element.count():
        print(f"{code} {year}年 Q{quarter} 季報 未找到資料")
        return False

    print(f"正在下載 {code} {year}年 Q{quarter} 季報...")
    
    success_q = False
    for retry_click in range(max_retries): # 增加「重新呼叫」機制
        try:
            with page.expect_popup(timeout=60000) as popup_info:
                link_element.click()
            
            pdf_page = popup_info.value
            from .common import get_pdf_from_popup
            content = get_pdf_from_popup(pdf_page, code, cool_down_base, max_retries)
            
            if content:
                save_path = Path(save_dir) / f"{year}_Q{quarter}_{code}.pdf"
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_bytes(content)
                print(f"已儲存: {save_path}")
                success_q = True
                break
            else:
                print(f"⚠️ 第 {retry_click+1}/{max_retries} 次嘗試失敗 (檔案處理中或限流)，關閉彈窗並重新呼叫...")
                try: pdf_page.close()
                except: pass
                time.sleep(cool_down_base)
        except Exception as e:
            print(f"{code} Q{quarter} 第 {retry_click+1}/{max_retries} 次點擊失敗: {e}")
            time.sleep(cool_down_base)
            
    return success_q
