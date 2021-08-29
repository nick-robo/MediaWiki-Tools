#%%
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re



class WikiSubsetter:
    def __init__(self, input_url: str):

        if input_url.strip() == '':
            raise ValueError('Empty wiki url')

        self.parsed_url = urlparse(input_url)

        if not self.parsed_url.scheme:
            self.parsed_url = urlparse('http://' + input_url)

        if not len(self.parsed_url.netloc.split(".")) > 1:
            raise ValueError(f'Invalid url: {input_url}')

        self.base_url = self.parsed_url.netloc

        match = None
        if self.parsed_url.path:
            match = re.match('\/(.*?)\/', self.parsed_url.path)

        self.page_name = match.group(1) if match else None
        

    def get_data(page) -> BeautifulSoup:

        page = requests.get(page)
        if not page.ok:
            raise Exception(f'Failed on page {page}')
        return BeautifulSoup(page.text, 'html.parser')

# %%
