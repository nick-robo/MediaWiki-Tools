# %%
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
from typing import Callable, Union
from itertools import combinations
import mwparserfromhell as mwp
from mediawiki import MediaWiki 


class WikiSubsetter:
    def __init__(self, input_url: str):
        """Create WikiSubsetter object from a MediaWiki page.

        Args:
            input_url (str): A url from the wiki to be subsetted.
            Preferrably the main page.
        """

        if input_url.strip() == '':
            raise ValueError('Empty wiki url')

        self.parsed_url = urlparse(input_url)

        if not self.parsed_url.scheme:
            self.parsed_url = urlparse('http://' + input_url)

        if not len(self.parsed_url.netloc.split(".")) > 1:
            raise ValueError(f'Invalid url: {input_url}')

        # get base url 
        self.base_url = self.parsed_url._replace(
            path='', params='', fragment=''
        ).geturl()

        # get page name (wiki.com/page_name/Page) from input
        match = None
        if self.parsed_url.path:
            path = self.parsed_url.path.replace('/', '%')
            match = re.match('%(.*?)%', path)

        self.page_name = match.group(1) if match else None

        page = requests.get(self.base_url)
        if not page.ok:
            raise Exception(
                f"Couldn't conntect to {self.base_url}"
            )

        # method 2: get page name from landing page
        if not self.page_name:
            path = urlparse(page.url).path.replace('/', '%')
            match = re.match('%(.*?)%', path)
            self.page_name = match.group(1) if match else None

        # method 3: search landing page for link to main page
        if not self.page_name:
            data = BeautifulSoup(page.text, 'html.parser')
            main = [x.get('href') for x in data.find_all('a')
                    if x and 'Main' in x.get('href')]
            self.page_name = main[0].split('/')[0] if main else None

        # ensure page name was found
        assert self.page_name is not None, 'Could not get page name\
                                            (wiki.com/page_name/Page)'

        self.page_base_url = self.base_url + '/' + self.page_name + '/'

        # try to get api

        # build target list
        # TODO: Research more targets
        targets = [
            self.base_url + '/wiki/api.php',
            self.base_url + '/w/api.php',
            self.page_base_url + 'api.php',
        ]

        for target in targets:
            try:
                self.mw = MediaWiki(target)
                self.api_url = target
                self.has_api = True
                break
            except Exception:
                continue
        else:
            self.mw = None
            self.has_api = False
            self.api_url = None
        

    def get_data(self, input: str) -> BeautifulSoup:
        # TODO: deal with url or category name
        if 'http' in input:
            page = requests.get(input)
        else:
            # get fragment if link
            input = input.split('/')[-1]
            if 'List' in input:
                url = self.page_base_url + input
            else:
                url = self.page_base_url + 'Category:' + input

            page = requests.get(url)
        if not page.ok:
            raise Exception(f'Failed on page {page}')
        return BeautifulSoup(page.text, 'html.parser')

    def get_pages(self, input_link: str, get_subcats: bool = False,
                  get_lists: bool = False, recursive: bool = False,
                  list_only: bool = False) -> list[str]:
        """Get the pages from a category or list of the wiki.

        Args:
            input_link (str): Url or name of category or list.

            get_subcats (bool, optional): If True, gets links from first
            level subcategories. Defaults to False.

            get_lists (bool, optional): Gets lists in addition to pages.
            Defaults to False.

            recursive (bool, optional): Recursively get links from
            subcategories. Defaults to False.

            list_only (bool, optional): Only get links that are lists.
            Assumption (slightly risky): Lists are on the first page.
            Defaults to False.

        Returns:
            list[str]: A list of pages.
        """

        pages = []
        data = self.get_data(input_link)

        # get page div if category
        content = data.find(id='mw-pages')
        is_category = True if content else False

        if is_category and not list_only:
            links = data.find_all('a')

            next_page = list(filter(lambda x: x.text == 'next page', links))

            # get pages from subcats
            if get_subcats and (s := data.find(id='mw-subcategories')):
                s = data.find(id='mw-subcategories')
                for input_link in s.find_all('a'):
                    if (h := input_link.get('href')) and 'Category' in h:
                        pages.extend(self.get_pages(
                            self.base_url + h,
                            get_subcats=recursive,
                            get_lists=get_lists,
                            recursive=recursive
                        ))

            if len(next_page) != 0:
                pages.extend(
                    self.get_pages(
                        self.base_url + next_page[0].get('href'),
                        get_lists=get_lists
                    )
                )
            filter_links: Callable[[str], bool] = lambda x: (
                x if get_lists else (x and 'List' not in x)
            )

            links = filter(
                filter_links,
                map(lambda x: x.get('href'), content.find_all('a'))
            )
        # get lists only
        elif is_category:
            # assumption: all lists are on first page (>200 lists)
            links = [h for x in content.find_all('a')
                     if (h := x.get('href')) and 'List_' in h]
        # if input_link is list
        else:
            content = data.find(id="mw-content-text").find_all('a')
            links = [x.get('href') for x in content
                     if len(x) == 1 and not x.get('class')]

        pages.extend(links)

        return list(set(pages))

    def get_set(self, categories: Union[list[str], str], operation: str,
                pages_list: list[str] = [], get_subcats: bool = False,
                use_lists: bool = False) -> list[str]:

        if operation not in ['union', 'intersection']:
            raise Exception(
                f"Invalid operation: {operation} \
                chose from following: ['union','intersection']"
            )

        page_set = set()
        operator = 'update' if operation == 'union' else 'intersection_update'

        # use lists to increase efficiency
        # caveat: slightly slower if list does not exist
        if use_lists and operation == 'intersection' and len(categories) > 1:
            combs = combinations(categories, 2)
            done = set()
            for comb in combs:
                # skip if both categories have been intersected
                if all([x in done for x in comb]):
                    continue
                lists = self.get_pages(comb[0], list_only=True)
                # replace underscore and remove plural ([:-1])
                # assumption: categories are english
                s = comb[1].replace('_', ' ').lower()
                s = s[:-1] if s[-1] == 's' else s
                # match category string s in lists
                lists = [x for x in lists
                         if s in x.lower().replace('_', ' ')]
                if lists:
                    # if list is not empty get links from the first one
                    # (should always be one result)
                    list_pages = self.get_pages(lists[0])
                    # if page_list is not empty, intersect
                    if pages_list:
                        pages_list = set(pages_list).intersection(list_pages)
                    else:
                        pages_list.extend(list_pages)
                    # remove list items from categories
                    done.update(comb)
            if len(done) == len(set(categories)):
                return list(pages_list)

        # edge cases
        if not categories:
            raise Exception('Invalid argument')
        elif len(categories) == 1:
            page_set.update(self.get_pages(categories[0]))
        elif type(categories) == str:
            page_set.update(self.get_pages(categories))
        else:
            for category in categories:
                if not page_set:
                    page_set.update(self.get_pages(category, get_subcats))
                    continue
                getattr(page_set, operator)(
                    self.get_pages(category, get_subcats))

        if pages_list:
            getattr(page_set, operator)(pages_list)

        return list(page_set)

    def get_info(pages: Union[list[str], str]):

        parsed_wikitext = mwp.parse(wikitext)
        # get params dict from parsed template
        p_dict = {(kv := p.split('=', 1))[
            0].strip(): kv[1].strip() for p in biobox.params}

# %%


ws = WikiSubsetter('www.***REMOVED***pedia.com')
cats = ['Caucasian', 'Asian']
# result_list = ws.get_set(cats, 'intersection',
#  use_lists=True)
result_naive = ws.get_set(cats, 'intersection')

# assert not set(result_naive) ^ set(result_list)
print('Done')

# %%
