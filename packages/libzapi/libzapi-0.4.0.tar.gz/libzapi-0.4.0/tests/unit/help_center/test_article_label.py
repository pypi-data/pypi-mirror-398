from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.article_label import ArticleLabel
from hypothesis import given

strategy = builds(
    ArticleLabel,
    name=just("cciiA"),
)


@given(strategy)
def test_session_logical_key_from_id(model: ArticleLabel):
    assert model.logical_key.as_str() == "article_label:cciia"
