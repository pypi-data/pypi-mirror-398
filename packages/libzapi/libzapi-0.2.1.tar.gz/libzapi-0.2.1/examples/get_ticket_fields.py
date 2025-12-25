"""
Example usage of libzapi for listing Zendesk ticket fields.

To run:
    uv run python examples.py
or, if using pip:
    python examples.py
"""

from domain.models.ticketing.ticket_field import TicketField
from domain.value_objects import Id
from libzapi import Ticketing
from libzapi.domain.errors import ZapiError

# Choose one auth method:
# 1) OAuth token:
# sdk = Zapi("https://acme.zendesk.com", oauth_token="YOUR_OAUTH_TOKEN")

# 2) Email + API token:
sdk = Ticketing(
    base_url="https://acme.zendesk.com",
    email="example@email.com",
    api_token="<your_api_token>",
)

try:
    print("=== Listing ticket fields ===")
    for f in sdk.ticket_fields.list_all():
        print(f"[{f.id.value}] {f.title} ({f.type}) required={f.required}")

    # Create a new field example
    new_field = TicketField(
        id=Id(0),  # placeholder, Zendesk assigns it
        key=None,
        title="Example Field",
        type="text",
        required=False,
        visible_in_portal=True,
    )

    print("\n=== Creating new ticket field ===")
    created = sdk.ticket_fields.create_field(new_field)
    print(f"Created field {created.title} with ID {created.id.value}")

    print("\n=== Deleting field back ===")
    sdk.ticket_fields.delete_field(created.id.value)
    print("Deleted successfully.")

except ZapiError as e:
    print("❌ Zendesk API error:", e)
