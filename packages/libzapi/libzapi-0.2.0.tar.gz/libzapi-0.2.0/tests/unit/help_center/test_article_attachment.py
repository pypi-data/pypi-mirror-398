from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.article_attachment import ArticleAttachment
from hypothesis import given

strategy = builds(
    ArticleAttachment,
    file_name=just("cciiA.csv"),
)


@given(strategy)
def test_session_logical_key_from_id(model: ArticleAttachment):
    assert model.logical_key.as_str() == "article_attachment:cciia.csv"
