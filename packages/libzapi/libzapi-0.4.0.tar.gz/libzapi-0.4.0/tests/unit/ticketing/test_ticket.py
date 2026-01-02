import pytest
from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.ticket import Ticket, User
from libzapi.infrastructure.api_clients.ticketing import TicketApiClient

strategy = builds(
    Ticket,
    id=just(222),
)


@given(strategy)
def test_logical_key_from_id(ticket):
    assert ticket.logical_key.as_str() == "ticket:222"


def test_user_props():
    user = User(
        id=123,
        name="John Doe",
    )

    assert user.id == 123
    assert user.name == "John Doe"


@pytest.mark.parametrize(
    "method_name, args, expected_path, return_value",
    [
        ("list", [], "/api/v2/tickets", "tickets"),
        ("list_organization", [456], "/api/v2/organizations/456/tickets", "tickets"),
        ("list_user_requested", [789], "/api/v2/users/789/tickets/requested", "tickets"),
        ("list_user_ccd", [101], "/api/v2/users/101/tickets/ccd", "tickets"),
        ("list_user_followed", [112], "/api/v2/users/112/tickets/followed", "tickets"),
        ("list_user_assigned", [131], "/api/v2/users/131/tickets/assigned", "tickets"),
        ("list_recent", [], "/api/v2/tickets/recent", "tickets"),
        ("list_collaborators", [141], "/api/v2/tickets/141/collaborators", "users"),
        ("list_followers", [151], "/api/v2/tickets/151/followers", "users"),
        ("list_email_ccs", [161], "/api/v2/tickets/161/email_ccs", "users"),
        ("list_incidents", [171], "/api/v2/tickets/171/incidents", "tickets"),
        ("list_problems", [], "/api/v2/tickets/problems", "tickets"),
        ("count", [], "/api/v2/tickets/count", "count"),
        ("organization_count", [201], "/api/v2/organizations/201/tickets/count", "count"),
        ("user_ccd_count", [211], "/api/v2/users/211/tickets/ccd/count", "count"),
        ("user_assigned_count", [221], "/api/v2/users/221/tickets/assigned/count", "count"),
        ("show_multiple_tickets", [[231, 232, 233]], "/api/v2/tickets/show_many?ids=231,232,233", "tickets"),
    ],
)
def test_ticket_api_client(method_name, args, expected_path, return_value, mocker):
    https = mocker.Mock()
    https.base_url = "https://example.zendesk.com"
    https.get.return_value = {return_value: []}

    client = TicketApiClient(https)

    method = getattr(client, method_name, None)
    list(method(*args))

    https.get.assert_called_with(expected_path)
