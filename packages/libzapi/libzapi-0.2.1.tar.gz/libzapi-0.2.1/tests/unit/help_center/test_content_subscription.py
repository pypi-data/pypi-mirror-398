from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.content_subscription import ContentSubscription
from hypothesis import given

strategy = builds(
    ContentSubscription,
    id=just("555"),
)


@given(strategy)
def test_session_logical_key_from_id(model: ContentSubscription):
    assert model.logical_key.as_str() == "content_subscription:id_555"
