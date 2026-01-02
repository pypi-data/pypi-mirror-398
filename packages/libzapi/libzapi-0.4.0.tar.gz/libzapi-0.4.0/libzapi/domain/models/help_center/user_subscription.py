from dataclasses import dataclass

from libzapi.domain.shared_objects.logical_key import LogicalKey


@dataclass(frozen=True, slots=True)
class UserSubscription:
    id: int
    follower_id: int
    followed_id: int

    @property
    def logical_key(self) -> LogicalKey:
        base = f"id_{self.id}"
        return LogicalKey("user_subscription", base)
