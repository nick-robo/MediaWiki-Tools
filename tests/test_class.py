"""Test module for MediaWikiTools class."""
from mwtools.mediawikitools import MediaWikiTools
import pytest
import requests
from deepdiff import DeepDiff

wiki_list = ('harrypotter.fandom.com',
             'https://en.wikivoyage.org/wiki/Main_Page',
             'https://en.uncyclopedia.co',
             'encyclopediaofmath.org/wiki/Main_Page')

wiki_list_no_api = ('https://proteopedia.org', 'https://www.werelate.org/')

invalid_list = ('google', 'https://google', 'https://google/search',
                'https://www.fakewiki.biz/', '	   ')


def assert_pagelist_equivalent(reslist1: list[str],
                               reslist2: list[str]) -> None:
	"""Check equivalence of pagelists.

	Args:
			reslist1 (list[str]): [description]
			reslist2 (list[str]): [description]
	"""
	# TODO: Flexibly check whether get pages results are equivalent
	# 			up to deletions and recent changes
	assert set(reslist1) == set(reslist2), \
                                      f'API and non-API results differ: \n\
					{DeepDiff(reslist1, reslist2, ignore_order=True)}'


@pytest.mark.parametrize('page', wiki_list)
def test_class_init_api(page):
	ws = MediaWikiTools(page)

	assert ws.has_api
	assert ws.mw
	assert ws.page_base_url


@pytest.mark.parametrize('page', wiki_list_no_api)
def test_class_init_no_api(page):
	ws = MediaWikiTools(page)

	assert not ws.has_api
	assert not ws.mw
	assert ws.page_base_url


@pytest.mark.parametrize('page', invalid_list)
def test_class_init_invalid(page):
	with pytest.raises(Exception):
		MediaWikiTools(page)


def test_class_get_pages():
	wikis = [
		'https://lgbt.wikia.org/wiki/Main_Page',
		'https://en.uncyclopedia.co',
		'https://harrypotter.fandom.com'
	]
	for wiki in wikis:
		if not requests.get(wiki, timeout=5).ok:
			pytest.skip(f'{wiki} seems to be down.')

	# assert raises exception if no api with wikia/fandom
	with pytest.raises(Exception):
		ws = MediaWikiTools('https://lgbt.wikia.org/wiki/Main_Page')
		ws.get_pages('https://lgbt.wikia.org/wiki/Category:1958_births',
		             use_api=False)

	with pytest.raises(Exception):
		ws = MediaWikiTools('harrypotter.fandom.com')
		ws.get_pages('Hogwarts_dropouts', use_api=False)

	# test get_pages
	ws = MediaWikiTools('https://en.uncyclopedia.co')
	cats = [
	    'Tribes of Britain',
	    'Tribes_of_Britain',
	    'https://en.uncyclopedia.co/wiki/Category:Tribes_of_Britain',
	]
	assert ws.has_api

	res_api = ws.get_pages(cats[0])
	res_no_api = ws.get_pages(cats[0], use_api=False)

	assert len(res_api) != 0
	assert_pagelist_equivalent(res_api, res_no_api)

	res = ws.get_pages(cats[1])
	assert_pagelist_equivalent(res_api, res)

	res = ws.get_pages(cats[2])
	assert_pagelist_equivalent(res_api, res)

	# test get_subcats
	res_api = ws.get_pages(cats[0], get_subcats=True)
	res_no_api = ws.get_pages(cats[0], get_subcats=True, use_api=False)

	assert res_api
	assert_pagelist_equivalent(res_api, res_no_api)

	# test recursive
	res_api = ws.get_pages(cats[0],
	                       get_subcats=True,
	                       with_subcats=True,
	                       recursive=True,
	                       use_api=True)

	res_no_api = ws.get_pages(cats[0],
	                          get_subcats=True,
	                          recursive=True,
	                          with_subcats=True,
	                          use_api=False)

	diff = DeepDiff(res_api, res_no_api, ignore_order=True)

	# check missing or added categories
	assert not diff.get('dictionary_item_removed')
	assert not diff.get('dictionary_item_added')

	# test no_api with paginated category
	ws = MediaWikiTools('en.wikipedia.org')
	cat = 'Italian_film_directors'

	res_api = ws.get_pages(cat, use_api=True)

	res_no_api = ws.get_pages(cat, use_api=False)

	assert res_api
	assert_pagelist_equivalent(res_api, res_no_api)

	# test get_lists
	cat = 'Lists_of_film_directors_by_nationality'
	res_api = ws.get_pages(cat, get_lists=True, use_api=True)
	res_no_api = ws.get_pages(cat, get_lists=True, use_api=False)

	assert res_api
	assert_pagelist_equivalent(res_api, res_no_api)

	# test list_only
	cat = 'https://en.wikipedia.org/wiki/Category:Azerbaijani_film_directors'
	res_api = ws.get_pages(cat, list_only=True, use_api=True)
	res_no_api = ws.get_pages(cat, list_only=True, use_api=False)

	assert res_api
	assert_pagelist_equivalent(res_api, res_no_api)


def test_get_set():
	if not requests.get('https://en.wikipedia.org', timeout=5).ok:
		pytest.skip('en.wikipedia.org seems to be down.')
	ws = MediaWikiTools('en.wikipedia.org')
	assert ws.has_api

	res_api = ws.get_set(['Countries in Asia', 'Countries_in_Europe'],
	                     operations='union')

	res_no_api = ws.get_set(['Countries in Asia', 'Countries_in_Europe'],
	                        operations='union',
	                        use_api=False)

	assert_pagelist_equivalent(res_api, res_no_api)

	res_api = ws.get_set(['Countries in Asia', 'Countries_in_Europe'],
	                     operations='&')

	res_no_api = ws.get_set(['Countries in Asia', 'Countries_in_Europe'],
	                        operations='&',
	                        use_api=False)

	assert_pagelist_equivalent(res_api, res_no_api)

	res_api = ws.get_set(['Countries in Asia', 'Countries_in_Europe'],
	                     operations='&',
	                     get_subcats=True)

	res_no_api = ws.get_set(['Countries in Asia', 'Countries_in_Europe'],
	                        operations='&',
	                        get_subcats=True,
	                        use_api=False)

	assert_pagelist_equivalent(res_api, res_no_api)
