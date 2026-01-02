from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.guide_media_object import Media
from hypothesis import given

strategy = builds(
    Media,
    name=just("cciiA"),
)


@given(strategy)
def test_session_logical_key_from_id(model: Media):
    assert model.logical_key.as_str() == "guide_media_object:cciia"
