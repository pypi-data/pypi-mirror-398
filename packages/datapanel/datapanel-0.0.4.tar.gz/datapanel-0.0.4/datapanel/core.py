import requests
from concurrent.futures import ThreadPoolExecutor
import os
from urllib.parse import unquote


class DataPanel:
    def __init__(self, params=None):
        if params is None:
            params = {}
        self.symbol = params.get('symbol')
        self.exchanges = params.get('exchanges', [])
        self.dataTypes = params.get('dataTypes', [])
        self.startDate = params.get('startDate')
        self.endDate = params.get('endDate')
        self.apiKey = params.get('apiKey')
        self.targetDir = params.get('targetDir')

    def download_file(self, url, download_dir='downloads', timeout=10):
        os.makedirs(download_dir, exist_ok=True)
        filename = unquote(url.split('/')[-1].split('?')[0])
        filepath = os.path.join(download_dir, filename)

        if os.path.exists(filepath):
            print(f"file exist, continue: {filename}")
            return

        try:
            with requests.get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):  # 分块写入
                        f.write(chunk)
            print(f"download: {filename}")
        except Exception as e:
            print(f"error: {url}: {str(e)}")

    def multi_thread_download(self, urls, download_dir='downloads', num_threads=4):
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            executor.map(lambda url: self.download_file(url, download_dir), urls)

    def get_download_urls(self):
        url = "https://datapanel.dev/api/file/download"
        params = {
            "exchanges": self.exchanges,
            "symbol": self.symbol,
            "dataTypes": self.dataTypes,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "apiKey": self.apiKey,
        }
        response = requests.post(url, json=params)
        if response.status_code == 200:
            return response.json().get("data", {}).get("downloadUrls", [])
        else:
            return []

    def download(self):
        urls = self.get_download_urls()
        self.multi_thread_download(urls, download_dir=self.targetDir)
