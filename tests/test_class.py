from app.classes import WikiSubsetter
import pytest


@pytest.mark.parametrize(
    'page', [

    ]
)
def test_WikiSubsetter_init(page):
    ws = WikiSubsetter(page)
    ws.get_data('')
