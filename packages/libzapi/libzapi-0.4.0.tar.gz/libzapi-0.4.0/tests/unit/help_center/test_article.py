from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.article import Article
from hypothesis import given

strategy = builds(
    Article,
    title=just("art123"),
)


@given(strategy)
def test_session_logical_key_from_id(model: Article):
    assert model.logical_key.as_str() == "article:art123"
