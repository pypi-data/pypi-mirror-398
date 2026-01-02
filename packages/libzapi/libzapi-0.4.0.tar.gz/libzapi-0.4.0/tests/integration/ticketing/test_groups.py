import uuid

from libzapi.application.commands.ticketing.group_cmds import CreateGroupCmd, UpdateGroupCmd
from libzapi import Ticketing


def test_list_groups(ticketing: Ticketing):
    groups = list(ticketing.groups.list_all())
    assert len(groups) > 0, "Expected at least one group from the live API"


def test_assignable_groups(ticketing: Ticketing):
    groups = list(ticketing.groups.list_assignable())
    assert len(groups) > 0, "Expected at least one assignable group from the live API"


def test_count_groups(ticketing: Ticketing):
    count_snapshot = ticketing.groups.count()
    assert count_snapshot.value > 0, "Expected group count to be greater than zero"


def test_create_update_delete_group(ticketing: Ticketing):
    # Create a new group
    random_id = str(uuid.uuid4())
    new_group = ticketing.groups.create(
        CreateGroupCmd(name=f"Test Group {random_id}", description="A group created for testing purposes")
    )
    assert new_group.id is not None, "Expected the created group to have an ID"

    # Update the group
    updated_group = ticketing.groups.update(
        new_group.id,
        UpdateGroupCmd(name=f"Updated Test Group {random_id}", description="An updated group for testing purposes"),
    )
    assert updated_group.name == f"Updated Test Group {random_id}", "Expected the group name to be updated"

    # Get the group by ID
    fetched_group = ticketing.groups.get_by_id(new_group.id)
    assert fetched_group.id == new_group.id, "Expected to fetch the same group by ID"

    # Delete the group
    ticketing.groups.delete(new_group.id)
