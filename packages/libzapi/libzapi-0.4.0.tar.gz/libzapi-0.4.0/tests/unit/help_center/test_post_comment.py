from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.post_comment import PostComment
from hypothesis import given

strategy = builds(
    PostComment,
    id=just(333),
)


@given(strategy)
def test_session_logical_key_from_id(model: PostComment):
    assert model.logical_key.as_str() == "post_comment:id_333"
