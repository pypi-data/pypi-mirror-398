from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.category import Category
from hypothesis import given

strategy = builds(
    Category,
    name=just("cciiA"),
)


@given(strategy)
def test_session_logical_key_from_id(model: Category) -> None:
    assert model.logical_key.as_str() == "category:cciia"
