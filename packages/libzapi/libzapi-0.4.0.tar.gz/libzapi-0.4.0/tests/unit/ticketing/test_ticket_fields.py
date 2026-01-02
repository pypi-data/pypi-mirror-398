from hypothesis import given
from hypothesis.strategies import integers, just, builds

from libzapi.domain.models.ticketing.ticket_field import CustomFieldText

ticket_field_strategy = builds(
    CustomFieldText,
    id=integers(min_value=1),
    raw_title=just("order_number"),
)


@given(ticket_field_strategy)
def test_ticket_field_logical_key_from_raw_title(ticket_field):
    assert ticket_field.logical_key.as_str() == "ticket_field:order_number"
