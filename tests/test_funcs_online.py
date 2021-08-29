import pytest
from app.functions import *
from functools import reduce


def test_get_set_intersection1():
    cats = [
        'https://www.***REMOVED***pedia.com/***REMOVED***s/Category:1968_births',
        'https://www.***REMOVED***pedia.com/***REMOVED***s/Category:Italian'
    ]
    result_naive = set(reduce(lambda x, y: x & y,
                              map(lambda x: set(get_***REMOVED***s(x)), cats)))
    result_function = get_set(categories=cats, operation='intersection')

    assert len(result_naive ^ set(result_function)) == 0


def test_get_set_intersection2():
    cats = [
        'https://www.***REMOVED***pedia.com/***REMOVED***s/Category:1968_births',
        'https://www.***REMOVED***pedia.com/***REMOVED***s/Category:Italian',
        'https://www.***REMOVED***pedia.com/***REMOVED***s/Category:Singers'
    ]
    result_naive = set(reduce(lambda x, y: x & y,
                              map(lambda x: set(get_***REMOVED***s(x)), cats)))
    result_function = get_set(categories=cats, operation='intersection')

    assert len(result_naive ^ set(result_function)) == 0


def test_get_set_union1():
    cats = [
        'https://www.***REMOVED***pedia.com/***REMOVED***s/Category:1968_births',
        'https://www.***REMOVED***pedia.com/***REMOVED***s/Category:1969_births'
    ]
    result_naive = set(reduce(lambda x, y: x | y,
                              map(lambda x: set(get_***REMOVED***s(x)), cats)))
    result_function = set(get_set(categories=cats, operation='union'))

    assert len(result_naive) == len(result_function)
    assert len(result_naive ^ result_function) == 0


def test_get_set_union2():
    a = 'https://www.***REMOVED***pedia.com/***REMOVED***s/Category:196'
    b = '_births'
    cats = [a + str(i) + b for i in range(10)]
    result_naive = set(reduce(lambda x, y: x | y,
                              map(lambda x: set(get_***REMOVED***s(x)), cats)))
    result_function = set(get_set(categories=cats, operation='union'))

    assert len(result_naive) == len(result_function)
    assert len(result_naive ^ result_function) == 0


def test_get_set_list_input():

    cat = 'https://www.***REMOVED***pedia.com/***REMOVED***s/Category:Turkish'
    link_list = ['/***REMOVED***s/Steve', '/***REMOVED***s/Bob']

    result_naive = set(get_***REMOVED***s(cat))
    result_func = set(get_set(
        categories=cat, operation='union', ***REMOVED***s_list=link_list
    ))

    assert len((result_naive | set(link_list)) ^ result_func) == 0

    link_list = ['/***REMOVED***s/Priscilla_Aydin', '/***REMOVED***s/Meral_Ertunc']

    result_func = set(
        get_set(
            categories=cat, operation='intersection',
            ***REMOVED***s_list=link_list
        )
    )

    assert len((result_naive & set(link_list)) ^ result_func) == 0


def test_get_***REMOVED***s_subcats():
    cat = 'https://www.***REMOVED***pedia.com/***REMOVED***s/Category:Eurasian'

    links = get_***REMOVED***s(category=cat, get_subcats=False)
    assert '/***REMOVED***s/Kassi_Nova' not in links

    links = get_***REMOVED***s(category=cat, get_subcats=True)
    assert '/***REMOVED***s/Kassi_Nova' in links
