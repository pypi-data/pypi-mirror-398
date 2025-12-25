from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.ticket_metric import TicketMetric

ticket_metric_strategy = builds(
    TicketMetric,
    id=just(333),
)


@given(ticket_metric_strategy)
def test_ticket_metric_logical_key_from_id(audit):
    assert audit.logical_key.as_str() == "ticket_metric:metric_333"
