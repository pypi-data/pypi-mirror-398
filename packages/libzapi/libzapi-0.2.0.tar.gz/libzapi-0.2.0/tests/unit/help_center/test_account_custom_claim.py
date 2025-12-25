from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.account_custom_claim import CustomClaim
from hypothesis import given

strategy = builds(
    CustomClaim,
    claim_identifier=just("cciiA"),
)


@given(strategy)
def test_session_logical_key_from_id(model: CustomClaim):
    assert model.logical_key.as_str() == "custom_claim:cciia"
