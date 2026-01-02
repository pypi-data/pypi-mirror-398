from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.workspace import Workspace

workspace_strategy = builds(
    Workspace,
    title=just("Base Workspace"),
)


@given(workspace_strategy)
def test_workspace_logical_key_from_id(schedule):
    assert schedule.logical_key.as_str() == "workspace:base_workspace"
