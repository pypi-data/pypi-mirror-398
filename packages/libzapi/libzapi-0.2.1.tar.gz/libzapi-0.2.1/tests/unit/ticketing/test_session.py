from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.sessions import Session

strategy = builds(
    Session,
    id=just("555"),
)


@given(strategy)
def test_session_logical_key_from_id(model: Session):
    assert model.logical_key.as_str() == "session:session_id_555"
