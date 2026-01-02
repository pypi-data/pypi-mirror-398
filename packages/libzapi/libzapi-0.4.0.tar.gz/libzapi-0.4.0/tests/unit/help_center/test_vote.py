from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.vote import Vote
from hypothesis import given

strategy = builds(
    Vote,
    id=just(123),
)


@given(strategy)
def test_session_logical_key_from_id(model: Vote) -> None:
    assert model.logical_key.as_str() == "vote:id_123"
