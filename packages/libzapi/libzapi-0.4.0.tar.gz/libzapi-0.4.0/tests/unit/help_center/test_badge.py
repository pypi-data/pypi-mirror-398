from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.badge import Badge
from hypothesis import given

strategy = builds(
    Badge,
    name=just("cciiA"),
)


@given(strategy)
def test_session_logical_key_from_id(model: Badge):
    assert model.logical_key.as_str() == "badge:cciia"
