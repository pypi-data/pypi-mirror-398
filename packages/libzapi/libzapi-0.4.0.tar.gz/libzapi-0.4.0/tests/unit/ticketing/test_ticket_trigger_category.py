from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.ticket_trigger_category import TicketTriggerCategory

strategy = builds(
    TicketTriggerCategory,
    name=just("CAT V"),
)


@given(strategy)
def test_trigger_category_logical_key_from_name(model: TicketTriggerCategory):
    assert model.logical_key.as_str() == "ticket_trigger_category:cat_v"
