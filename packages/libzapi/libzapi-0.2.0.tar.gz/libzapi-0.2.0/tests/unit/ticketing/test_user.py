import pytest
from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.user import User
from libzapi.infrastructure.api_clients.ticketing import UserApiClient

strategy = builds(
    User,
    id=just(123),
)


@given(strategy)
def test_logical_key_from_id(obj: User):
    assert obj.logical_key.as_str() == "user:id_123"


def test_user_api_client_get_one(mocker):
    fake_id = 12345
    https = mocker.Mock()
    https.base_url = "https://example.zendesk.com"
    https.get.return_value = {"user": {}}

    mocker.patch(
        "libzapi.infrastructure.api_clients.ticketing.user_api_client.to_domain",
        return_value=mocker.Mock(),  # does not matter what it is
    )

    client = UserApiClient(https)

    client.get(fake_id)

    https.get.assert_called_with(f"/api/v2/users/{fake_id}")


@pytest.mark.parametrize(
    "method_name, resource_type, filter_value, path",
    [
        ("list_all", None, None, "/api/v2/users"),
        ("list_by_group", "group_id", 123, "/api/v2/groups/123/users"),
        ("list_by_organization", "organization_id", 145, "/api/v2/organizations/145/users"),
    ],
)
def test_suspended_ticket_api_client_list_all(mocker, method_name, resource_type, filter_value, path):
    https = mocker.Mock()
    https.base_url = "https://example.zendesk.com"
    https.get.return_value = {"users": []}

    client = UserApiClient(https)

    method = getattr(client, method_name, None)
    if filter_value is not None:
        list(method(filter_value))
    else:
        list(method())

    https.get.assert_called_with(path)
