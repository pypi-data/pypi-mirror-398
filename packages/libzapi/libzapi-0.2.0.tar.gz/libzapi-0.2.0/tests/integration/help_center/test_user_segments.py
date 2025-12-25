from libzapi import HelpCenter


def test_list_user_segments_and_get(help_center: HelpCenter):
    user_segments = list(help_center.user_segments.list_all())
    assert len(user_segments) > 0, "Expected at least one section from the live API"
