from app.classes import WikiSubsetter
import pytest
from deepdiff import DeepDiff

wiki_list = ('harrypotter.fandom.com',
             'https://en.wikivoyage.org/wiki/Main_Page',
             'https://en.uncyclopedia.co',
             'encyclopediaofmath.org/wiki/Main_Page')

wiki_list_no_api = ('https://proteopedia.org', 'https://www.werelate.org/')


@pytest.fixture()
def check_pagelist_equal(reslist1: list[str], reslist2: list[str]) -> None:
	pass


@pytest.mark.parametrize('page', wiki_list)
def test_class_init_api(page):
	ws = WikiSubsetter(page)

	assert ws.has_api
	assert ws.mw
	assert ws.page_base_url


@pytest.mark.parametrize('page', wiki_list_no_api)
def test_class_init_no_api(page):
	ws = WikiSubsetter(page)

	assert not ws.has_api
	assert not ws.mw
	assert ws.page_base_url


def test_class_get_pages():
	ws = WikiSubsetter('https://en.uncyclopedia.co')
	cats = [
	    'Your Mom',
	    'Your_Mom',
	    'https://en.uncyclopedia.co/wiki/Category:Your_Mom',
	]
	assert ws.has_api

	res_api = ws.get_pages(cats[0])
	res_no_api = ws.get_pages(cats[0], use_api=False)

	assert len(res_api) != 0
	assert len(set(res_api) ^ set(res_no_api)) == 0

	assert len(set(res_api) ^ set(ws.get_pages(cats[1]))) == 0

	assert len(set(res_api) ^ set(ws.get_pages(cats[2]))) == 0

	# test get_subcats
	res_api = ws.get_pages(cats[0], get_subcats=True)
	res_no_api = ws.get_pages(cats[0], get_subcats=True, use_api=False)

	assert res_api
	assert len(set(res_api) ^ set(res_no_api)) == 0

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

	diff = DeepDiff(res_api,
	                res_no_api,
	                ignore_order=True)

	assert not diff.get('dictionary_item_removed')
	assert not diff.get('dictionary_item_added')
