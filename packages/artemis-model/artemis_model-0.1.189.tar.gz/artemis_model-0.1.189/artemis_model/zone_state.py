"""Zone state data models."""

# models/zone_state.py

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declared_attr

from artemis_model.base import CustomSyncBase, TimeStampMixin, CustomBase


class ZoneStateMetaMixin(TimeStampMixin):
    """
    Rarely changing part of a zone's state.
    One row per zone.
    """

    zone_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("zone.id", ondelete="CASCADE"),
        primary_key=True,
        default=uuid.uuid4,
        doc="Zone identifier (PK)",
    )

    player_mode: Mapped[str] = mapped_column(
        String, default="scheduled", nullable=False, index=True
    )
    player_state: Mapped[str] = mapped_column(String, default="ready", nullable=False, index=True)
    pp_details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    schedule_details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    @declared_attr
    def now_playing(cls) -> Mapped["ZoneNowPlaying"]:
        return relationship(
            "ZoneNowPlaying",
            back_populates="meta",
            uselist=False,
            cascade="all, delete-orphan",
        )


class ZoneStateMetaSync(CustomSyncBase, ZoneStateMetaMixin):
    pass


class ZoneStateMeta(CustomBase, ZoneStateMetaMixin):
    pass


class ZoneNowPlayingMixin:
    """
    Frequently changing part of a zone's state.
    Keep row narrow; PK-only index for cheap updates.
    One row per zone (FK to ZoneStateMeta).
    """

    zone_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("zone_state_meta.zone_id", ondelete="CASCADE"),
        primary_key=True,
        doc="Matches zone_state_meta.zone_id",
    )

    track_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    artist_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    album_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    playlist_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Lightweight timestamp for freshness; mirrors your style (see LoginHistory)
    updated_at = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def meta(cls) -> Mapped["ZoneStateMeta"]:
        return relationship("ZoneStateMeta", back_populates="now_playing")


class ZoneNowPlayingSync(CustomSyncBase, ZoneNowPlayingMixin):
    pass


class ZoneNowPlaying(CustomBase, ZoneNowPlayingMixin):
    pass
