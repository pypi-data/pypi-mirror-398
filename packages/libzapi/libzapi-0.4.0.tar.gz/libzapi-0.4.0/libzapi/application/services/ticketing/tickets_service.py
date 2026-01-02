from typing import Iterable

from libzapi.application.commands.ticketing.ticket_cmds import CreateTicketCmd, UpdateTicketCmd, TicketCmd
from libzapi.domain.models.ticketing.ticket import Ticket, User, CustomField
from libzapi.domain.shared_objects.count_snapshot import CountSnapshot
from libzapi.infrastructure.api_clients.ticketing.ticket_api_client import TicketApiClient


class TickestService:
    """High-level service using the API client."""

    def __init__(self, client: TicketApiClient) -> None:
        self._client = client

    def list(self) -> Iterable[Ticket]:
        return self._client.list()

    def list_organization(self, organization_id: int) -> Iterable[Ticket]:
        return self._client.list_organization(organization_id=organization_id)

    def list_user_requested(self, user_id: int) -> Iterable[Ticket]:
        return self._client.list_user_requested(user_id=user_id)

    def list_user_ccd(self, user_id: int) -> Iterable[Ticket]:
        return self._client.list_user_ccd(user_id=user_id)

    def list_user_followed(self, user_id: int) -> Iterable[Ticket]:
        return self._client.list_user_followed(user_id=user_id)

    def list_user_assigned(self, user_id: int) -> Iterable[Ticket]:
        return self._client.list_user_assigned(user_id=user_id)

    def list_recent(self) -> Iterable[Ticket]:
        return self._client.list_recent()

    def list_collaborators(self, ticket_id: int) -> Iterable[User]:
        return self._client.list_collaborators(ticket_id=ticket_id)

    def list_followers(self, ticket_id: int) -> Iterable[User]:
        return self._client.list_followers(ticket_id=ticket_id)

    def list_email_ccs(self, ticket_id: int) -> Iterable[User]:
        return self._client.list_email_ccs(ticket_id=ticket_id)

    def list_incidents(self, ticket_id: int) -> Iterable[Ticket]:
        return self._client.list_incidents(ticket_id=ticket_id)

    def list_problems(self) -> Iterable[Ticket]:
        return self._client.list_problems()

    def get(self, ticket_id: int) -> Ticket:
        return self._client.get(ticket_id=ticket_id)

    def count(self) -> CountSnapshot:
        return self._client.count()

    def organization_count(self, organization_id: int) -> CountSnapshot:
        return self._client.organization_count(organization_id=organization_id)

    def user_ccd_count(self, user_id: int) -> CountSnapshot:
        return self._client.user_ccd_count(user_id=user_id)

    def user_assigned_count(self, user_id: int) -> CountSnapshot:
        return self._client.user_assigned_count(user_id=user_id)

    def create(self, subject: str,
               description: str,
               tags: Iterable[str] = (),
               custom_fields: Iterable[dict] = (),
               priority: str = "",
               ticket_type: str = "",
               group_id: int = None,
               requester_id: int = None,
               organization_id: int = None,
               problem_id: int = None,
               ticket_form_id: int = None,
               brand_id: int = None,
               ) -> Ticket:
        fields = []
        for custom_field in custom_fields:
            field = CustomField(
                id=custom_field["id"],
                value=custom_field["value"]
            )
            fields.append(field)

        entity = self.cast_to_ticket_command(CreateTicketCmd, brand_id, description, fields, group_id, organization_id, priority,
                                             problem_id, requester_id, subject, tags, ticket_form_id, ticket_type)
        return self._client.create_ticket(entity=entity)

    @staticmethod
    def cast_to_ticket_command(cmd_type, brand_id: int | None, description: str, fields: Iterable[CustomField], group_id: int | None,
                               organization_id: int | None, priority: str, problem_id: int | None,
                               requester_id: int | None, subject: str, tags: Iterable[str], ticket_form_id: int | None,
                               ticket_type: str) -> TicketCmd:
        entity = cmd_type(
            subject=subject,
            custom_fields=fields,
            description=description,
            priority=priority,
            type=ticket_type,
            group_id=group_id,
            requester_id=requester_id,
            organization_id=organization_id,
            problem_id=problem_id,
            tags=tags,
            ticket_form_id=ticket_form_id,
            brand_id=brand_id,
        )
        return entity

    def show_multiple_tickets(self, ticket_ids: Iterable[int]) -> Iterable[Ticket]:
        return self._client.show_multiple_tickets(ticket_ids=ticket_ids)

    def update(self, ticket_id:int, subject: str = None,
               description: str = None,
               tags: Iterable[str] = (),
               custom_fields: Iterable[dict] = (),
               priority: str = "",
               ticket_type: str = "",
               group_id: int = None,
               requester_id: int = None,
               organization_id: int = None,
               problem_id: int = None,
               ticket_form_id: int = None,
               brand_id: int = None,
               ) -> Ticket:
        fields = []
        for custom_field in custom_fields:
            field = CustomField(
                id=custom_field["id"],
                value=custom_field["value"]
            )
            fields.append(field)

        entity = self.cast_to_ticket_command(UpdateTicketCmd, brand_id, description, fields, group_id, organization_id, priority,
                                             problem_id, requester_id, subject, tags, ticket_form_id, ticket_type)
        return self._client.update_ticket(ticket_id=ticket_id, entity=entity)

    def create_many(self, dict_input: Iterable[dict]) -> Iterable[Ticket]:
        entity = []
        for item in dict_input:
            record = self.cast_to_ticket_command(CreateTicketCmd,
                brand_id=item.get("brand_id"),
                description=item["description"],
                fields=[CustomField(id=cf["id"], value=cf["value"]) for cf in item.get("custom_fields", [])],
                group_id=item.get("group_id"),
                organization_id=item.get("organization_id"),
                priority=item.get("priority", ""),
                problem_id=item.get("problem_id"),
                requester_id=item.get("requester_id"),
                subject=item["subject"],
                tags=item.get("tags", ()),
                ticket_form_id=item.get("ticket_form_id"),
                ticket_type=item.get("type", "")
            )
            entity.append(record)
        return self._client.create_many(entity=entity)
