import pytest
from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.email_notification import EmailNotification
from libzapi.infrastructure.api_clients.ticketing import EmailNotificationApiClient

strategy = builds(
    EmailNotification,
    notification_id=just(123),
)


@given(strategy)
def test_logical_key_from_id(obj: EmailNotification):
    assert obj.logical_key.as_str() == "email_notification:id_123"


def test_suspended_ticket_api_client_get_one(mocker):
    fake_id = 12345
    https = mocker.Mock()
    https.base_url = "https://example.zendesk.com"
    https.get.return_value = {"email_notification": {}}

    mocker.patch(
        "libzapi.infrastructure.api_clients.ticketing.email_notification_api_client.to_domain",
        return_value=mocker.Mock(),  # does not matter what it is
    )

    client = EmailNotificationApiClient(https)

    client.get(fake_id)

    https.get.assert_called_with(f"/api/v2/email_notifications/{fake_id}")


@pytest.mark.parametrize(
    "method_name,filter_type, filter_value",
    [
        ("list_by_notification_id", "notification_id", 123),
        ("list_by_comment_id", "comment_id", 456),
        ("list_by_ticket_id", "ticket_id", 789),
    ],
)
def test_suspended_ticket_api_client_list_all(mocker, method_name, filter_type, filter_value):
    https = mocker.Mock()
    https.base_url = "https://example.zendesk.com"
    https.get.return_value = {"email_notification": []}

    client = EmailNotificationApiClient(https)

    method = getattr(client, method_name, None)
    list(method(filter_value))

    https.get.assert_called_with(f"/api/v2/email_notifications?filter=[{filter_type}]={filter_value}")
