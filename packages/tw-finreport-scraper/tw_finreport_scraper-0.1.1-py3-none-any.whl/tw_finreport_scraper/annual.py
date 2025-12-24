import time
from pathlib import Path
from .common import BASE_URL, wait_for_rate_limit, get_pdf_from_popup

DOC_TYPES = {
    "F04": "股東會年報",
    "F17": "年報前十大股東相互間關係表",
    "F05": "股東會議事錄",
}

def crawl_all_annual_reports(page, year, code, save_dir_base, cool_down_base=30, max_retries=10):
    """
    優化後的抓取方式：一次開啟該股票該年度的所有文件列表，減少請求次數。
    返回失敗的 dtype 列表。
    """
    failed_dtypes = []
    target_dtypes = ["F04", "F17", "F05"]
    
    # 不帶 dtype 參數，一次顯示所有文件
    url = f"{BASE_URL}?step=1&colorchg=1&co_id={code}&year={year}&mtype=F"
    page.goto(url, wait_until="domcontentloaded")
    
    if not wait_for_rate_limit(page, code, cool_down_base, max_retries):
        return target_dtypes # 全部算失敗

    for dtype in target_dtypes:
        folder_name = DOC_TYPES.get(dtype)
        save_dir = Path(save_dir_base) / folder_name
        save_dir.mkdir(parents=True, exist_ok=True)

        # 定位 readfile2 連結
        # 這裡使用 xpath 同時檢查 dtype
        selector = f"//a[contains(@href, 'javascript:readfile2') and contains(@href, '{dtype}')]"
        link_element = page.locator(selector).first
        
        if not link_element.count():
            print(f"{code} {year}年 {folder_name} 未找到資料")
            failed_dtypes.append(dtype)
            continue

        print(f"正在下載 {code} {year}年 {folder_name}...")
        
        success_this_dtype = False
        for retry_click in range(max_retries): # 增加「重新呼叫」機制，最多嘗試 max_retries 次點擊
            try:
                with page.expect_popup(timeout=60000) as popup_info:
                    link_element.click()
                
                pdf_page = popup_info.value
                content = get_pdf_from_popup(pdf_page, code, cool_down_base, max_retries)
                
                if content:
                    save_path = save_dir / f"{year}_{code}_{folder_name}.pdf"
                    save_path.write_bytes(content)
                    print(f"已儲存: {save_path}")
                    success_this_dtype = True
                    break
                else:
                    print(f"⚠️ 第 {retry_click+1}/{max_retries} 次嘗試失敗 (檔案處理中或限流)，關閉彈窗並重新呼叫...")
                    try: pdf_page.close()
                    except: pass
                    time.sleep(cool_down_base) # 重新呼叫前小休一下
            except Exception as e:
                print(f"第 {retry_click+1}/{max_retries} 次點擊發生錯誤: {e}")
                time.sleep(cool_down_base)

        if not success_this_dtype:
            failed_dtypes.append(dtype)
            
        # 每次下載完小休一下，避免彈窗開太快
        import random
        time.sleep(random.uniform(2, 4))

    return failed_dtypes
