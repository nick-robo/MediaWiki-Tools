from app.functions import get_set, get_pages
from functools import reduce


def test_get_set_intersection1():
    cats = [
        'https://handwiki.org/wiki/\
            Category:Android_(operating_system)_development_software',
        'https://handwiki.org/wiki/Category:MacOS_programming_tools'
    ]
    result_naive = set(reduce(lambda x, y: x & y,
                              map(lambda x: set(get_pages(x)), cats)))
    result_function = get_set(categories=cats, operation='intersection')

    assert len(result_naive ^ set(result_function)) == 0


def test_get_set_intersection2():
    cats = [
        'https://handwiki.org/wiki/\
            Category:Android_(operating_system)_development_software',
        'https://handwiki.org/wiki/Category:MacOS_programming_tools',
        'https://handwiki.org/wiki/Category:Linux_programming_tools'
    ]
    result_naive = set(reduce(lambda x, y: x & y,
                              map(lambda x: set(get_pages(x)), cats)))
    result_function = get_set(categories=cats, operation='intersection')

    assert len(result_naive ^ set(result_function)) == 0


def test_get_set_union1():
    cats = [
        'https://handwiki.org/wiki/\
            Category:Android_(operating_system)_development_software',
        'https://handwiki.org/wiki/Category:MacOS_programming_tools'
    ]
    result_naive = set(reduce(lambda x, y: x | y,
                              map(lambda x: set(get_pages(x)), cats)))
    result_function = set(get_set(categories=cats, operation='union'))

    assert len(result_naive) == len(result_function)
    assert len(result_naive ^ result_function) == 0


def test_get_set_list_input():

    cat = 'https://handwiki.org/wiki/Category:Linux_programming_tools'
    link_list = ['/wiki/Steve', '/wiki/Bob']

    result_naive = set(get_pages(cat))
    result_func = set(get_set(
        categories=cat, operation='union', pages_list=link_list
    ))

    assert len((result_naive | set(link_list)) ^ result_func) == 0

    link_list = ['/wiki/Priscilla_Aydin', '/wiki/Meral_Ertunc']

    result_func = set(
        get_set(
            categories=cat, operation='intersection',
            pages_list=link_list
        )
    )

    assert len((result_naive & set(link_list)) ^ result_func) == 0


def test_get_pages_subcats():
    cat = 'https://handwiki.org/wiki/Category:Linux_programming_tools'

    links = get_pages(category=cat, get_subcats=False)
    assert '/wiki/HBasic' not in links and 'wiki/Software:BlueJ' in links

    links = get_pages(category=cat, get_subcats=True)
    assert '/wiki/HBasic' in links and 'wiki/Software:BlueJ' in links
