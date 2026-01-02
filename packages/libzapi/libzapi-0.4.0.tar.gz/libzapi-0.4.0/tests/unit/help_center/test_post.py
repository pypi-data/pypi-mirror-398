from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.post import Post
from hypothesis import given

strategy = builds(
    Post,
    title=just("cciiA"),
)


@given(strategy)
def test_session_logical_key_from_id(model: Post):
    assert model.logical_key.as_str() == "post:cciia"
