from libzapi.domain.shared_objects.field_definition import FieldDefinition, ShortFieldDefinition


def field_definition_mapper(data: dict) -> FieldDefinition | None:
    return FieldDefinition(
        id=data["id"],
        title=data["title"],
        type=data["type"],
        url=data["url"],
        filterable=data["filterable"],
        sortable=data["sortable"],
        order=data["order"],
    )


def short_field_definition_mapper(data: dict) -> ShortFieldDefinition | None:
    return ShortFieldDefinition(
        id=data["id"],
        title=data["title"],
        filterable=data["filterable"],
        sortable=data["sortable"],
    )
