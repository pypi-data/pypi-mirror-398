from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.ticket_trigger import TicketTrigger

strategy = builds(
    TicketTrigger,
    raw_title=just("Trigger Test"),
)


@given(strategy)
def test_ticket_trigger_logical_key_from_raw_title(model: TicketTrigger):
    assert model.logical_key.as_str() == "ticket_trigger:trigger_test"
