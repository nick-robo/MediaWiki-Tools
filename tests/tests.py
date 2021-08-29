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


def test_get_***REMOVED***s_subcats():
    cat = 'https://www.***REMOVED***pedia.com/***REMOVED***s/Category:Eurasian'
    links = get_***REMOVED***s(category=cat, get_subcats=True)

    assert ['/***REMOVED***s/' + x for x in ['Azra_Akin',
                                    'Kassi_Nova', 'Leyla_Stacked']] in links
