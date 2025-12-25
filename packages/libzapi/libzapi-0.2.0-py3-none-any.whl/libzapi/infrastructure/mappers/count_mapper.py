from libzapi.domain.shared_objects.count_snapshot import CountSnapshot


def to_count_snapshot(data: dict) -> CountSnapshot:
    """Maps a count snapshot dictionary to an integer count."""
    return CountSnapshot(
        refreshed_at=data["refreshed_at"],
        value=data["value"],
    )
