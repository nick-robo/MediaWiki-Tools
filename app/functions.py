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


def get_***REMOVED***s(category: str, get_subcats: bool = False,
              get_lists: bool = False) -> list[str]:

    base_url = 'https://www.***REMOVED***pedia.com'
    ***REMOVED***s = []

    page = requests.get(category)
    if not page.ok:
        raise Exception(f'Failed on page {category}')
    data = BeautifulSoup(page.text, 'html.parser')
    links = data.find_all('a')

    next_page = list(filter(lambda x: x.text == 'next page', links))

    # get ***REMOVED***s from subcats
    if get_subcats and (s := data.find(id='mw-subcategories')) is not None:
        s = data.find(id='mw-subcategories')
        for link in s.find_all('a'):
            if (href := link.get('href')) is not None and 'Category' in href:
                ***REMOVED***s.extend(get_***REMOVED***s(base_url + href))

    if len(next_page) != 0:
        ***REMOVED***s.extend(get_***REMOVED***s(base_url + next_page[0].get('href')))

    content = data.find(id='mw-pages')

    filter_links: Callable[[str], bool] = lambda x: (
        (x is not None) if get_lists else ('List' not in x and x is not None)
    )

    links = filter(
        filter_links,
        map(lambda x: x.get('href'), content.find_all('a'))
    )

    ***REMOVED***s.extend(links)
    ***REMOVED***s = list(set(***REMOVED***s))

    return ***REMOVED***s

# %%


def get_active(***REMOVED***s: list[str]) -> list[str]:
    """Finds active models

    Args:
        ***REMOVED***s (list): A list in the format ['/***REMOVED***s/Model_A',
                                            '/***REMOVED***s/Model_B', ...]

    Returns:
        list: A list of active models
    """

    active_***REMOVED***s = []

    base_url = 'https://www.***REMOVED***pedia.com'

    for ***REMOVED*** in ***REMOVED***s:
        page = requests.get(base_url + ***REMOVED***)
        if not page.ok:
            raise Exception(f'Invalid ***REMOVED***: {***REMOVED***}')
        data = BeautifulSoup(page.text)

        candidates = data.find(class_='infobox').find_all('td')
        years_active = [x for x in candidates if 'Years' in x.text]

        if len(years_active) != 0:
            years = years_active[0].find_next('td').text
            years = re.split('-|—|–', years)
            years = [x.strip() for x in years if x.strip() != '']
            if len(years) >= 2 and not years[-1].isnumeric():
                active_***REMOVED***s.append(***REMOVED***)
                print(f'Active:{years}\t\t{***REMOVED***}')
            elif len(years) >= 2:
                print(f'Inactive:{years}\t\t{***REMOVED***}')
                continue
            else:
                pass

    return active_***REMOVED***s

# %%

# get a subset or superset of a list of categories


def get_set(categories: Union[list[str], str], operation: str,
            ***REMOVED***s_list: Optional[list[str]] = None,
            get_subcats: bool = False) -> list:

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
        ***REMOVED***_set.update(get_***REMOVED***s(categories[0]))
    elif type(categories) == str:
        ***REMOVED***_set.update(get_***REMOVED***s(categories))
    else:
        for category in categories:
            if not ***REMOVED***_set:
                ***REMOVED***_set.update(get_***REMOVED***s(category, get_subcats))
                continue
            getattr(***REMOVED***_set, operator)(get_***REMOVED***s(category, get_subcats))

    if ***REMOVED***s_list is not None:
        getattr(***REMOVED***_set, operator)(***REMOVED***s_list)

    return list(***REMOVED***_set)
