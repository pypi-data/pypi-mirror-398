from datetime import datetime

from libzapi.domain.models.ticketing.group import Group
from libzapi.infrastructure.mappers.ticketing.group_mapper import to_payload_create
from libzapi.infrastructure.serialization.parse import to_domain


def test_mapper_to_domain_and_back_payload_roundtrip():
    raw = {
        "id": 301,
        "name": "Support Team",
        "description": "Handles customer support tickets",
        "is_public": True,
        "default": False,
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-02T12:00:00Z",
        "url": "https://example.zendesk.com/api/v2/groups/301.json",
        "deleted": False,
    }
    entity = to_domain(raw, Group)
    assert entity.id == 301
    assert entity.name == "Support Team"
    assert entity.description == "Handles customer support tickets"
    assert entity.is_public is True

    payload = to_payload_create(entity)
    assert payload == {
        "group": {
            "name": "Support Team",
            "description": "Handles customer support tickets",
            "is_public": True,
            "default": False,
        }
    }


def test_group_logical_key():
    group = Group(
        id=302,
        name="Engineering",
        description="Engineering Department",
        is_public=False,
        created_at=datetime.fromisoformat("2022-01-01T12:00:00Z"),
        updated_at=datetime.fromisoformat("2022-01-01T12:00:00Z"),
        url="https://example.zendesk.com/api/v2/groups/302.json",
        default=False,
        deleted=False,
    )
    assert group.logical_key.as_str() == "group:engineering"
