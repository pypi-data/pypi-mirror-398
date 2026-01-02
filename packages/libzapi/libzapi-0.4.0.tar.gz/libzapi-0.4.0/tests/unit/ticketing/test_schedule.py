from hypothesis import given
from hypothesis.strategies import just, builds

from libzapi.domain.models.ticketing.schedule import Schedule, Holiday

schedule_strategy = builds(
    Schedule,
    name=just("USA Schedule"),
)

holiday_strategy = builds(
    Holiday,
    name=just("New Year"),
)


@given(schedule_strategy)
def test_schedule_logical_key_from_id(schedule):
    assert schedule.logical_key.as_str() == "schedule:usa_schedule"


@given(holiday_strategy)
def test_holiday_logical_key_from_id(holiday):
    assert holiday.logical_key.as_str() == "schedule_holiday:new_year"
