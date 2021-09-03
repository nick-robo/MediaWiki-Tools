# Legacy functions from original development


# %%
import requests
from bs4 import BeautifulSoup
from typing import Callable, Optional, Union
import re


def get_data(page) -> BeautifulSoup:
    page = requests.get(page)
    if not page.ok:
        raise Exception(f'Failed on page {page}')
    return BeautifulSoup(page.text, 'html.parser')


def get_pages(category: str, get_subcats: bool = False,
              get_lists: bool = False) -> list[str]:

    base_url = 'https://www.pagepedia.com'
    pages = []

    page = requests.get(category)
    if not page.ok:
        raise Exception(f'Failed on page {category}')
    data = BeautifulSoup(page.text, 'html.parser')
    links = data.find_all('a')

    next_page = list(filter(lambda x: x.text == 'next page', links))

    # get pages from subcats
    if get_subcats and (s := data.find(id='mw-subcategories')) is not None:
        s = data.find(id='mw-subcategories')
        for link in s.find_all('a'):
            if (href := link.get('href')) is not None and 'Category' in href:
                pages.extend(get_pages(base_url + href))

    if len(next_page) != 0:
        pages.extend(get_pages(base_url + next_page[0].get('href')))

    content = data.find(id='mw-pages')

    filter_links: Callable[[str], bool] = lambda x: (
        (x is not None) if get_lists else ('List' not in x and x is not None)
    )

    links = filter(
        filter_links,
        map(lambda x: x.get('href'), content.find_all('a'))
    )

    pages.extend(links)
    pages = list(set(pages))

    return pages

# %%


def get_active(pages: list[str]) -> list[str]:
    """Finds active models

    Args:
        pages (list): A list in the format ['/pages/Page_A',
                                            '/pages/Page_B', ...]

    Returns:
        list: A list of active models
    """

    active_pages = []

    base_url = 'https://www.pagepedia.com'

    for page in pages:
        page = requests.get(base_url + page)
        if not page.ok:
            raise Exception(f'Invalid page: {page}')
        data = BeautifulSoup(page.text)

        candidates = data.find(class_='infobox').find_all('td')
        years_active = [x for x in candidates if 'Years' in x.text]

        if len(years_active) != 0:
            years = years_active[0].find_next('td').text
            years = re.split('-|—|–', years)
            years = [x.strip() for x in years if x.strip() != '']
            if len(years) >= 2 and not years[-1].isnumeric():
                active_pages.append(page)
                print(f'Active:{years}\t\t{page}')
            elif len(years) >= 2:
                print(f'Inactive:{years}\t\t{page}')
                continue
            else:
                pass

    return active_pages

# %%

# get a subset or superset of a list of categories


def get_set(categories: Union[list[str], str], operation: str,
            pages_list: Optional[list[str]] = None,
            get_subcats: bool = False) -> list:

    if operation not in ['union', 'intersection']:
        raise Exception(
            f"Invalid operation: {operation} \
              chose from following: ['union','intersection']"
        )

    page_set = set()
    operator = 'update' if operation == 'union' else 'intersection_update'

    # edge cases
    if len(categories) == 0:
        raise Exception('Invalid argument')
    elif len(categories) == 1:
        page_set.update(get_pages(categories[0]))
    elif type(categories) == str:
        page_set.update(get_pages(categories))
    else:
        for category in categories:
            if not page_set:
                page_set.update(get_pages(category, get_subcats))
                continue
            getattr(page_set, operator)(get_pages(category, get_subcats))

    if pages_list is not None:
        getattr(page_set, operator)(pages_list)

    return list(page_set)
