from app.classes import WikiSubsetter
import pytest

wiki_list = (
    'harrypotter.fandom.com',
    'https://en.wikivoyage.org/wiki/Main_Page',
    'https://en.uncyclopedia.co',
    'encyclopediaofmath.org/wiki/Main_Page'
)

wiki_list_no_api = (
    'https://proteopedia.org',
    'https://www.werelate.org/'
)


@pytest.mark.parametrize('page', wiki_list)
def test_class_init_api(page):
    ws = WikiSubsetter(page)

    assert ws.has_api
    assert ws.mw
    assert ws.page_base_url


@pytest.mark.parametrize('page', wiki_list_no_api)
def test_class_init_api2(page):
    ws = WikiSubsetter(page)

    assert not ws.has_api
    assert not ws.mw
    assert ws.page_base_url


def test_class_get_pages():
    ws = WikiSubsetter('https://en.wikivoyage.org/wiki/Main_Page')
    cats = [
        'Europe itineraries',
        'Europe_itineraries',
        'https://en.wikivoyage.org/wiki/Category:Europe_itineraries',
    ]
    assert ws.has_api

    res_api = ws.get_pages(cats[0])
    res_no_api = ws.get_pages(cats[0], use_api=False)

    assert len(res_api) != 0
    assert len(set(res_api) ^ set(res_no_api)) == 0

    assert len(
        set(res_api) ^ set(ws.get_pages(cats[1]))
    ) == 0

    assert len(
        set(res_api) ^ set(ws.get_pages(cats[2]))
    ) == 0
