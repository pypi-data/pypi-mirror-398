from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.ticket_audit import TicketAudit

ticket_audit_strategy = builds(
    TicketAudit,
    id=just(222),
)


@given(ticket_audit_strategy)
def test_ticket_audit_logical_key_from_id(audit):
    assert audit.logical_key.as_str() == "ticket_audit:ticket_audit_222"
