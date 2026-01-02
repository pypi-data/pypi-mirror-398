import pytest

from hypothesis.strategies import builds, just

from libzapi.domain.models.help_center.user_segment import UserSegment
from libzapi.application.commands.help_center.user_segments_cmds import CreateUserSegmentCmd, UserType
from hypothesis import given

strategy = builds(
    UserSegment,
    name=just("cciiA"),
)


@given(strategy)
def test_session_logical_key_from_id(model: UserSegment) -> None:
    assert model.logical_key.as_str() == "user_segment:cciia"


def test_create_user_segment_command_fail():
    with pytest.raises(ValueError):
        CreateUserSegmentCmd(
            name="Test Segment",
            user_type=UserType("no-user-allowed"),  # Invalid user_type
        )


def test_create_user_segment_command_success():
    cmd = CreateUserSegmentCmd(name="Test Segment", user_type=UserType("signed_in_users"))
    assert cmd.name == "Test Segment"
    assert cmd.user_type.value == "signed_in_users"
