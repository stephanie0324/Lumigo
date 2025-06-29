
import requests
import urllib3
import os
from scihub import SciHub
from bs4 import BeautifulSoup
from urllib.parse import urljoin


from logger import logger
from .data_utils import load_and_process_pdf_async

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _create_scihub():
    """建立 SciHub 實例（設定 timeout）"""
    sh = SciHub()
    sh.timeout = 30
    return sh

# def search_by_doi(doi: str) -> dict:
#     """
#     根據 DOI 搜尋論文，回傳基本資訊與 PDF 下載網址

#     Args:
#         doi (str): 論文 DOI 編號

#     Returns:
#         dict: 包含 title, author, year, pdf_url 等資訊
#     """
#     sh = _create_scihub()
#     try:
#         result = sh.fetch(doi)
#         return {
#             'doi': doi,
#             'pdf_url': result['url'],
#             'status': 'success',
#             'title': result.get('title', ''),
#             'author': result.get('author', ''),
#             'year': result.get('year', '')
#         }
#     except Exception as e:
#         return {
#             'doi': doi,
#             'status': 'error',
#             'message': str(e)
#         }


def download_pdf_from_scihub_page(scihub_url: str, save_path: str) -> bool:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        logger.info(f"[SciHub] Requesting page: {scihub_url}")
        resp = requests.get(scihub_url, headers=headers, timeout=20, verify=False)
        if resp.status_code != 200:
            logger.warning(f"[SciHub] Page request failed: {scihub_url} (status {resp.status_code})")
            return False

        soup = BeautifulSoup(resp.content, "html.parser")
        iframe = soup.find("iframe")
        if not iframe or not iframe.get("src"):
            logger.warning(f"[SciHub] No iframe found on page: {scihub_url}")
            return False

        pdf_url = iframe["src"]
        if pdf_url.startswith("//"):
            pdf_url = "https:" + pdf_url
        else:
            pdf_url = urljoin(scihub_url, pdf_url)

        logger.info(f"[SciHub] Downloading PDF from: {pdf_url}")
        pdf_resp = requests.get(pdf_url, headers=headers, timeout=30, verify=False)
        if pdf_resp.status_code != 200:
            logger.warning(f"[SciHub] PDF download failed (status {pdf_resp.status_code})")
            return False
        if b"%PDF" not in pdf_resp.content[:1024]:
            logger.warning(f"[SciHub] Downloaded content is not a PDF")
            return False

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(pdf_resp.content)
        logger.info(f"[SciHub] PDF saved to: {save_path}")
        return True

    except Exception as e:
        logger.error(f"[SciHub] Exception during PDF download: {e}")
        return False

def search_by_doi(doi: str, pdf_save_dir: str = "./pdfs") -> dict:
    sh = _create_scihub()
    try:
        result = sh.fetch(doi)
        pdf_page_url = result.get('url')
        if not pdf_page_url:
            raise ValueError("SciHub did not return a PDF page URL")

        # 用 DOI 做成安全的檔名
        safe_filename = doi.replace("/", "_") + ".pdf"
        save_path = os.path.join(pdf_save_dir, safe_filename)

        success = download_pdf_from_scihub_page(pdf_page_url, save_path)
        if not success:
            raise RuntimeError("Failed to download PDF from SciHub page")

        return {
            'doi': doi,
            'status': 'success',
            'title': result.get('title', ''),
            'author': result.get('author', ''),
            'year': result.get('year', ''),
            'pdf_path': save_path,
            'pdf_url': pdf_page_url,
        }
    except Exception as e:
        logger.error(f"search_by_doi error: {e}")
        return {
            'doi': doi,
            'status': 'error',
            'message': str(e)
        }

def search_by_title(title: str) -> dict:
    """
    根據論文標題使用 CrossRef 查詢 DOI 並回傳 PDF 等資訊

    Args:
        title (str): 論文標題

    Returns:
        dict: 與 search_by_doi 結果類似
    """
    try:
        url = f"https://api.crossref.org/works?query.title={title}&rows=1"
        response = requests.get(url, timeout=15)
        data = response.json()
        items = data.get('message', {}).get('items', [])
        if items:
            doi = items[0].get('DOI')
            if doi:
                return search_by_doi(doi)
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
    return {'status': 'not_found', 'title': title}

def search_by_keyword(keyword: str, num_results: int = 5) -> list:
    """
    根據關鍵字搜尋論文列表（透過 CrossRef + DOI 抓 PDF）

    Args:
        keyword (str): 搜尋關鍵字
        num_results (int): 最多回傳幾筆結果

    Returns:
        list: 每筆都是 search_by_doi 結果格式
    """
    results = []
    try:
        url = f"https://api.crossref.org/works?query={keyword}&rows={num_results}"
        response = requests.get(url, timeout=120)
        data = response.json()
        items = data.get('message', {}).get('items', [])
        for item in items:
            doi = item.get('DOI')
            if doi:
                paper = search_by_doi(doi)
                print(paper)
                if paper.get("status") == "success":
                    results.append(paper)
    except Exception as e:
        return [{'status': 'error', 'message': str(e)}]
    return results
