"""Sync state model for tracking data syncer progress."""

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from artemis_model.base import CustomBase, CustomSyncBase


class SyncStateMixin:
    """Mixin for sync state tracking."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(nullable=True)
    total_synced: Mapped[int] = mapped_column(nullable=False, default=0)
    total_failed: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    last_error: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)


class SyncStateSync(CustomSyncBase, SyncStateMixin):
    """Sync version of SyncState model."""

    pass


class SyncState(CustomBase, SyncStateMixin):
    """
    Tracks the sync state for data syncer operations.

    Attributes:
        table_name: Name of the source table being synced
        last_sync_at: Timestamp of last sync attempt
        last_successful_sync_at: Timestamp of last successful sync (used for incremental sync)
        total_synced: Cumulative count of records synced
        total_failed: Cumulative count of failed records
        status: Current status (pending, running, completed, failed)
        last_error: Last error message if any
    """

    pass

