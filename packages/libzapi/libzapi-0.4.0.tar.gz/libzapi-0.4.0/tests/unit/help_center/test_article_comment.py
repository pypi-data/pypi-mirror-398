from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.article_comment import ArticleComment
from hypothesis import given

strategy = builds(
    ArticleComment,
    id=just(123),
)


@given(strategy)
def test_session_logical_key_from_id(model: ArticleComment):
    assert model.logical_key.as_str() == "article_comment:id_123"
