from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.management_permission_group import PermissionGroup
from hypothesis import given

strategy = builds(
    PermissionGroup,
    name=just("cciiA"),
)


@given(strategy)
def test_session_logical_key_from_id(model: PermissionGroup):
    assert model.logical_key.as_str() == "permission_group:cciia"
