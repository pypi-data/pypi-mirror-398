from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.badge_category import BadgeCategory
from hypothesis import given

strategy = builds(
    BadgeCategory,
    name=just("cciiA"),
)


@given(strategy)
def test_session_logical_key_from_id(model: BadgeCategory):
    assert model.logical_key.as_str() == "badge_category:cciia"
