from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.support_address import RecipientAddress

strategy = builds(
    RecipientAddress,
    name=just("mailbox"),
)


@given(strategy)
def test_model_logical_key_from_id(model: RecipientAddress) -> None:
    assert model.logical_key.as_str() == "support_address:mailbox"
