from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.sla_policies import SlaPolicy

strategy = builds(
    SlaPolicy,
    title=just("Sample"),
)


@given(strategy)
def test_session_logical_key_from_id(model: SlaPolicy):
    assert model.logical_key.as_str() == "sla_policy:sample"
