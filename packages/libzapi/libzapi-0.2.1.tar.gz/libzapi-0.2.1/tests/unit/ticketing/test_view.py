from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.view import View

view_strategy = builds(
    View,
    raw_title=just("Base View"),
)


@given(view_strategy)
def test_view_logical_key_from_raw_title(view):
    assert view.logical_key.as_str() == "view:base_view"
