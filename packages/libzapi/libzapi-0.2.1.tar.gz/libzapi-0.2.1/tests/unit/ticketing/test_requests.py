from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.request import Request

request_strategy = builds(
    Request,
    id=just(123),
)


@given(request_strategy)
def test_request_logical_key_from_id(request):
    assert request.logical_key.as_str() == "request:request_123"
