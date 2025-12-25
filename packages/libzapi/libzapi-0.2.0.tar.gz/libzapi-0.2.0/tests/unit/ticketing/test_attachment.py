from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.attachment import Attachment
from libzapi.infrastructure.api_clients.ticketing import AttachmentApiClient

strategy = builds(
    Attachment,
    file_name=just("ANdroid.png"),
)


@given(strategy)
def test_logical_key_from_id(attachment):
    assert attachment.logical_key.as_str() == "attachment:android.png"


def test_ticket_api_client(mocker):
    fake_id = 12345
    https = mocker.Mock()
    https.base_url = "https://example.zendesk.com"
    https.get.return_value = {"attachment": {}}

    mocker.patch(
        "libzapi.infrastructure.api_clients.ticketing.attachment_api_client.to_domain",
        return_value=mocker.Mock(),  # does not matter what it is
    )

    client = AttachmentApiClient(https)

    client.get(fake_id)

    https.get.assert_called_with(f"/api/v2/attachments/{fake_id}")
