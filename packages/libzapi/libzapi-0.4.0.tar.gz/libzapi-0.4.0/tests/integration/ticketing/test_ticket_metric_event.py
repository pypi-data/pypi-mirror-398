from libzapi import Ticketing


def test_list_ticket_metric_events(ticketing: Ticketing):
    events = ticketing.ticket_metric_events.list(start_time=1)
    # get the first 100 events lazily
    first_10000 = [event for _, event in zip(range(10000), events)]
    assert len(first_10000) > 0
    for event in first_10000:
        assert event.id is not None
        assert event.ticket_id is not None
        assert event.metric is not None
        assert event.instance_id is not None
        assert event.type is not None
        assert event.time is not None
        assert event.deleted is not None
