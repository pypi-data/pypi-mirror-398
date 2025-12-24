"""SQS messages."""

from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import UUID


from artemis_model.schedule import ScheduleItem
from pydantic import BaseModel, Field

from artemis_model.zone_activity import ZoneActivityType


class Action(str, Enum):
    """Message type enum."""

    CALCULATE_ALL_SCHEDULES = "calculate-all-schedules"
    TRIAGE_SCHEDULE = "triage-schedule"
    TRIGGER_DATABASE_MIGRATION = "trigger-database-migration"
    MOVE_TIME_SLOT = "move-time-slot"
    PUSH_PLAYLIST = "push-playlist"
    EXPIRE_PUSHED_PLAYLIST = "expire-pushed-playlist"
    REFRESH_TRACK_BUCKET = "refresh-track-bucket"
    RECALCULATE_SCHEDULE = "recalculate-schedule"
    PLAYER_MODE_CHANGE = "player-mode-change"
    BAN_TRACK = "ban-track"
    ZONE_ACTIVITY = "zone-activity"
    STOP_MUSIC = "stop-music"
    EXPIRE_LICENCE = "expire-licence"
    REMOVE_ACTIVE_DEVICE = "remove-active-device"


class BaseMessage(BaseModel):
    """Base message for incoming messages schema."""

    ts: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp value of the message",
    )
    action: Action


class MoveTimeSlotIn(BaseMessage):
    """Move to time slot message schema."""

    action: Action = Action.MOVE_TIME_SLOT
    zone_id: int
    bucket_key: str
    playlist_ids: list[int]


class StopMusicIn(BaseMessage):
    """Stop music message schema."""

    action: Action = Action.STOP_MUSIC
    zone_id: int


class TriageScheduleIn(BaseMessage):
    """Triage schedule message schema."""

    action: Action = Action.TRIAGE_SCHEDULE
    schedule: list[ScheduleItem]


class CalculateAllSchedulesIn(BaseMessage):
    """Calculate all schedules message schema."""

    action: Action = Action.CALCULATE_ALL_SCHEDULES


class PushPlaylistIn(BaseMessage):
    """Push playlist message schema."""

    action: Action = Action.PUSH_PLAYLIST
    zone_id: int
    playlist_ids: list[int]
    expire_at: datetime | None = Field(
        default=None, description="The datetime that the playlist will expire"
    )


class PushPlaylistExpireIn(BaseMessage):
    """Push playlist expire message schema."""

    action: Action = Action.EXPIRE_PUSHED_PLAYLIST
    zone_id: int
    new_mode: Literal["pushplaylist", "scheduled"] = "scheduled"
    bucket_key: str | None = None


class RefreshTrackBucketIn(BaseMessage):
    """Refresh track bucket message schema."""

    action: Action = Action.REFRESH_TRACK_BUCKET
    zone_id: int
    bucket_key: str


class RecalculateScheduleIn(BaseMessage):
    """Recalculate schedule message schema."""

    action: Action = Action.RECALCULATE_SCHEDULE
    zone_id: int


class BanTrackIn(BaseMessage):
    """Ban track message schema."""

    action: Action = Action.BAN_TRACK
    zone_id: int
    track_id: UUID
    playlist_id: int
    bucket_key: str


class ZoneActivityIn(BaseMessage):
    """Zone activity message schema."""

    action: Action = Action.ZONE_ACTIVITY
    zone_id: int
    activity_type: ZoneActivityType
    activity_data: dict


class ExpireLicenceIn(BaseMessage):
    """Expire licence message schema."""

    action: Action = Action.EXPIRE_LICENCE
    organization_id: UUID


class RemoveActiveDeviceIn(BaseMessage):
    """Remove active device message schema."""

    action: Action = Action.REMOVE_ACTIVE_DEVICE
    zone_id: int
    device_id: str
    reason: str = Field(
        default="websocket_disconnect",
        description="Reason for device removal (websocket_disconnect, shutdown, etc.)",
    )
