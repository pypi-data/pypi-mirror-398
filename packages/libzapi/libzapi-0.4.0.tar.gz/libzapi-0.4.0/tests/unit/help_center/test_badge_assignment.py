from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.badge_assignment import BadgeAssignment
from hypothesis import given

strategy = builds(
    BadgeAssignment,
    id=just("234"),
)


@given(strategy)
def test_session_logical_key_from_id(model: BadgeAssignment):
    assert model.logical_key.as_str() == "badge_assignment:id_234"
