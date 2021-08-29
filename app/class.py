import requests
from bs4 import BeautifulSoup
from typing import Callable, Optional, Union
import re
import io
from urllib.parse import urlparse


class Wiki:
    def __init__(self, input_url: str):

        if input_url.strip() is '':
            raise ValueError('Empty wiki url')

        if 'http' not in input_url:
            input_url = 'https://' + input_url

        self.parsed_url = urlparse(input_url)
        self.base_url = self.parsed_url.netloc

        if self.parsed_url.path:
            
            pass

    def get_data(page) -> BeautifulSoup:

        page = requests.get(page)
        if not page.ok:
            raise Exception(f'Failed on page {page}')
        return BeautifulSoup(page.text, 'html.parser')
