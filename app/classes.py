# %%
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote
import re
from typing import Union
from itertools import combinations
# import mwparserfromhell as mwp
from mediawiki import MediaWiki


class WikiSubsetter:
    def __init__(self, input_url: str):
        """Create WikiSubsetter object from a MediaWiki page.

        Args:
            input_url (str): A url from the wiki to be subsetted.
            Preferrably the main page or api.
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
            r = [h for x in data.find_all('a')
                 if (h := x.get('href')) and 'Main' in h]
            self.page_name = r[0].split('/')[0] if r else None

        # method 4: last ditch attempt
        if not self.page_name:
            r = [
                # find /page_name/Page links and get page_name
                h[1] for x in data.find_all('a')
                if (h := x.get('href')) and len(h := h.split('/')) == 3
            ]
            # get most frequent page name
            self.page_name = max(set(r), key=r.count) if r else None

        # ensure page name was found
        assert self.page_name, 'Could not get page name\
                                (wiki.com/page_name/Page)\n\
                                Try input an article page'

        self.page_base_url = self.base_url + '/' + self.page_name + '/'

        # try to get api
        # build target list
        # TODO: Research more targets
        targets = [
            input_url if 'api' in input_url else None,
            self.base_url + '/wiki/api.php',
            self.base_url + '/api.php',
            self.base_url + '/w/api.php',
            self.page_base_url + 'api.php',
        ]

        for target in targets:
            # skip None
            if not target:
                continue

            # TODO: Find faster way than creating object
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

    def get_data(self, input: str,
                 print_pretty: bool = False) -> BeautifulSoup:
        if 'http' in input:
            page = requests.get(input)
        else:
            # get fragment if incomplete url and url encode it
            input = quote(input.split('/')[-1].replace(' ', '_'))
            page = requests.get(self.page_base_url + 'Category:' + input)

            # if not category
            if not page.ok:
                page = requests.get(
                    self.page_base_url + input
                )

        if not page.ok:
            raise Exception(f'Failed on page {page}')

        data = BeautifulSoup(page.text, 'html.parser')
        if print_pretty:
            print()
        return data

    def get_pages(self, input_link: str,
                  get_subcats: bool = False,
                  get_lists: bool = False,
                  recursive: bool = False,
                  list_only: bool = False,
                  use_api: bool = True) -> list[str]:
        """Get the pages from a category or list of the wiki.

        Args:
            input_link (str): Url or name of category or list.

            get_subcats (bool, optional): If True, gets links from first \
                level subcategories. Defaults to False.

            get_lists (bool, optional): Gets lists in addition to pages. \
                Assumption (problematic): list has 'List_' in name \
                Defaults to False.

            recursive (bool, optional): Recursively get links from \
                subcategories. Defaults to False.

            list_only (bool, optional): Only get links that are lists. \
                Assumption (slightly risky, only no api): \
                Lists are on the first page. \
                Defaults to False.

            use_api (bool, optional): Whether to use the api (if present). \
                Defaults to true.

        Returns:
            list[str]: A list of pages.
        """

        if self.has_api and use_api:
            # TODO: Figure out method for lists
            name = ''

            if any(
                [x in input_link for x in self.base_url.split('/') if x]
            ):
                i = input_link.split('/').index(self.page_name)
                name = '/'.join(input_link.split('/')[i+1:])

            name = input_link if not name else name
            pages, subcats = self.mw.categorymembers(
                name,
                results=None
            )
            if (get_subcats or recursive):
                for cat in subcats:
                    pages.extend(
                        self.get_pages(
                            cat,
                            get_subcats=recursive,
                            recursive=recursive
                        )
                    )

            if not get_lists:
                pages = [
                    p for p in pages if 'List ' not in p and
                    'File:' not in p
                ]
            elif list_only:
                pages = [
                    p for p in pages if 'List ' in p and
                    'File:' not in p
                ]
            else:
                pages = [
                    p for p in pages if 'File:' not in p
                ]
            return pages

        if any([x in self.base_url for x in ['wikia.', 'fandom.com']]):
            raise NotImplementedError(
                'Web scraping not implemented for wikia/fandom.com'
            )

        pages = []
        data = self.get_data(input_link)

        # get page div if category
        content = data.find(id='mw-pages')
        is_category = True if content else False

        if is_category and not list_only:
            links = data.find_all('a')

            next_page = list(filter(lambda x: x.text == 'next page', links))

            # get pages from subcats
            if (get_subcats or recursive) and (s := data.find(id='mw-subcategories')):
                for input_link in s.find_all('a'):
                    if (h := input_link.get('href')) and 'Category' in h:
                        pages.extend(self.get_pages(
                            self.base_url + h,
                            get_subcats=recursive,
                            get_lists=get_lists,
                            recursive=recursive,
                            use_api=use_api
                        ))

            if len(next_page) != 0:
                pages.extend(
                    self.get_pages(
                        self.base_url + next_page[0].get('href'),
                        get_lists=get_lists,
                        use_api=use_api
                    )
                )

            links = [
                link.text for link in content.find_all('a')
                # check href not None and if it is a page link
                if (h := link.get('href')) and self.page_name in h and
                # filter lists if get_lists is false
                (True if get_lists else 'List ' not in link.text)
            ]

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

        operation_dict = {
            'intersection': 'intersection_update',
            'i': 'intersection_update',
            'and': 'intersection_update',
            '&': 'intersection_update',
            'union': 'update',
            'u': 'update',
            'or': 'update',
            '|': 'update'
        }

        if operation not in operation_dict.keys():
            raise Exception(
                f"Invalid operation: {operation} \
                chose from following: \n\t{operation_dict.keys()}"
            )

        page_set = set()
        operator = operation_dict[operation]

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
        pass
        # parsed_wikitext = mwp.parse(wikitext)
        # get params dict from parsed template
        # p_dict = {(kv := p.split('=', 1))[
        #     0].strip(): kv[1].strip() for p in biobox.params}
# %%
