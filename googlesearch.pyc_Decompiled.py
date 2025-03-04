# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: googlesearch.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

from settings import *
import requests
from bs4 import BeautifulSoup as bs
import json
import re

class GoogleSearch:

    def __init__(self):
        self.url = 'https://www.googleapis.com/customsearch/v1'
        self.google_api_key = GOOGLE_SEARCH_API_KEY
        self.goolge_cse_id = GOOGLE_CSE_ID

    def search_google(self, keyword):
        main_keyword = keyword.main_keyword
        params = {'key': self.google_api_key, 'cx': self.goolge_cse_id, 'q': main_keyword}
        res = requests.get(self.url, params=params)
        content = json.loads(res.content)
        link_li = []
        for item in content['items']:
            link_li.append(item['link'])
        for link in link_li:
            text_extracted = self.get_link_content(link)
            if text_extracted:
                keyword.google_search_result.append(text_extracted)
                if len(keyword.google_search_result) >= 2:
                    break

    def get_link_content(self, link):
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        headers = {'User-Agent': user_agent}
        res = requests.get(url=link, headers=headers)
        if res.status_code == 200:
            content = res.content
            soup = bs(content, 'html.parser')
            important_text = []
            title = soup.title.string if soup.title else ''
            important_text.append(title)
            for tag in soup.find_all(['h1', 'h2', 'h3']):
                important_text.append(tag.get_text(strip=True))
            for tag in soup.find_all('p'):
                important_text.append(tag.get_text(strip=True))
            link_text = '\n'.join(filter(None, important_text))
            link_text = re.sub('\\n+', '\n', link_text)
            print(link_text)
            return link_text