from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.user_subscription import UserSubscription
from hypothesis import given

strategy = builds(
    UserSubscription,
    id=just(2111),
)


@given(strategy)
def test_session_logical_key_from_id(model: UserSubscription):
    assert model.logical_key.as_str() == "user_subscription:id_2111"
