from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.topic import Topic
from hypothesis import given

strategy = builds(
    Topic,
    name=just("cciiA"),
)


@given(strategy)
def test_session_logical_key_from_id(model: Topic) -> None:
    assert model.logical_key.as_str() == "topic:cciia"
