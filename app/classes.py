# %%
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
from typing import Callable, Union, Optional


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

        # get page name (wiki.com/page_name/Page) from input
        match = None
        if self.parsed_url.path:
            path = self.parsed_url.path.replace('/', '%')
            match = re.match('%(.*?)%', path)

        self.page_name = match.group(1) if match else None
        self.base_url = self.parsed_url._replace(
            path='', params='', fragment=''
        ).geturl()

        page = requests.get(self.base_url)
        if not page.ok:
            raise Exception(
                f"Couldn't conntect to {self.base_url}"
            )

        # get page name from main page
        if not self.page_name:
            path = urlparse(page.url).path.replace('/', '%')
            match = re.match('%(.*?)%', path)
            self.page_name = match.group(1)

    def get_data(self, page) -> BeautifulSoup:
        # TODO: deal with url or category name
        page = requests.get(page)
        if not page.ok:
            raise Exception(f'Failed on page {page}')
        return BeautifulSoup(page.text, 'html.parser')

    def get_pages(self, category: str, get_subcats: bool = False,
                  get_lists: bool = False) -> list[str]:

        pages = []
        data = self.get_data(category)
        links = data.find_all('a')

        next_page = list(filter(lambda x: x.text == 'next page', links))

        # get pages from subcats
        if get_subcats and (s := data.find(id='mw-subcategories')) is not None:
            s = data.find(id='mw-subcategories')
            for link in s.find_all('a'):
                if (h := link.get('href')) is not None and 'Category' in h:
                    pages.extend(self.get_pages(self.base_url + h))

        if len(next_page) != 0:
            pages.extend(
                self.get_pages(self.base_url + next_page[0].get('href'))
            )

        content = data.find(id='mw-pages')

        filter_links: Callable[[str], bool] = lambda x: (
            (x is not None) if get_lists else (
                'List' not in x and x is not None)
        )

        links = filter(
            filter_links,
            map(lambda x: x.get('href'), content.find_all('a'))
        )

        pages.extend(links)
        pages = list(set(pages))

        return pages

    def get_set(self, categories: Union[list[str], str], operation: str,
                pages_list: Optional[list[str]] = None,
                get_subcats: bool = False) -> list[str]:

        if operation not in ['union', 'intersection']:
            raise Exception(
                f"Invalid operation: {operation} \
                chose from following: ['union','intersection']"
            )

        ***REMOVED***_set = set()
        operator = 'update' if operation == 'union' else 'intersection_update'

        # edge cases
        if len(categories) == 0:
            raise Exception('Invalid argument')
        elif len(categories) == 1:
            ***REMOVED***_set.update(self.get_pages(categories[0]))
        elif type(categories) == str:
            ***REMOVED***_set.update(self.get_pages(categories))
        else:
            for category in categories:
                if not ***REMOVED***_set:
                    ***REMOVED***_set.update(self.get_pages(category, get_subcats))
                    continue
                getattr(***REMOVED***_set, operator)(
                    self.get_pages(category, self.get_subcats))

        if pages_list is not None:
            getattr(***REMOVED***_set, operator)(pages_list)

        return list(***REMOVED***_set)
# %%
