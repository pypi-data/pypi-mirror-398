from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.content_tag import ContentTag
from hypothesis import given

strategy = builds(
    ContentTag,
    name=just("cciiA"),
)


@given(strategy)
def test_session_logical_key_from_id(model: ContentTag):
    assert model.logical_key.as_str() == "content_tag:cciia"
