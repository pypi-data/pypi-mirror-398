from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.brand import Brand

strategy = builds(
    Brand,
    name=just("ACME"),
)


@given(strategy)
def test_session_logical_key_from_id(model: Brand):
    assert model.logical_key.as_str() == "brand:acme"
