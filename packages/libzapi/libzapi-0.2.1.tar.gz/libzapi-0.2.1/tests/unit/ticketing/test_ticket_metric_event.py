import pytest
from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.ticket_metric_event import TicketMetricEvent
from libzapi.infrastructure.api_clients.ticketing import TicketMetricEventApiClient

strategy = builds(
    TicketMetricEvent,
    id=just(222),
)


@given(strategy)
def test_logical_key_from_id(event):
    assert event.logical_key.as_str() == "ticket_metric_event:metric_event_id_222"


@pytest.mark.parametrize(
    "method_name, args, expected_path",
    [
        ("list", [1], "/api/v2/incremental/ticket_metric_events?start_time=1"),
    ],
)
def test_ticket_api_client(method_name, args, expected_path, mocker):
    https = mocker.Mock()
    https.base_url = "https://example.zendesk.com"
    https.get.return_value = {
        "ticket_metric_events": [
            {
                "id": 123,
                "ticket_id": 1,
                "metric": "agent_work_time",
                "instance_id": 0,
                "type": "measure",
                "time": "2023-10-28T02:11:02Z",
                "deleted": False,
            },
            {
                "id": 124,
                "ticket_id": 1,
                "metric": "reply_time",
                "instance_id": 1,
                "type": "update_status",
                "time": "2023-10-28T03:12:50Z",
                "deleted": False,
                "status": {"business": 61, "calendar": 61},
            },
            {
                "id": 125,
                "ticket_id": 1,
                "metric": "group_ownership_time",
                "instance_id": 1,
                "type": "apply_group_sla",
                "time": "2023-11-21T17:43:55Z",
                "deleted": False,
                "group_sla": {
                    "target": 1440,
                    "business_hours": False,
                    "policy": {"id": "PPP", "title": "Sample Title", "description": "SLA Sample"},
                },
            },
            {
                "id": 126,
                "ticket_id": 1,
                "metric": "requester_wait_time",
                "instance_id": 1,
                "type": "apply_sla",
                "time": "2024-07-19T00:59:21Z",
                "deleted": False,
                "sla": {
                    "target": 300,
                    "business_hours": False,
                    "policy": {"id": 3, "title": "SLA Teste", "description": None},
                    "target_in_seconds": 18000,
                },
            },
        ]
    }

    client = TicketMetricEventApiClient(https)

    method = getattr(client, method_name, None)
    list(method(*args))

    https.get.assert_called_with(expected_path)
