import uuid
from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declared_attr

from artemis_model.base import CustomSyncBase, TimeStampMixin, AuditMixin, CustomBase


class ApprovedPlaylistListMixin(TimeStampMixin, AuditMixin):
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization.id"), nullable=False, index=True
    )

    @declared_attr
    def organization(cls) -> Mapped["Organization"]:
        return relationship("Organization", back_populates="approved_playlist_lists")

    @declared_attr
    def playlist_associations(cls) -> Mapped[List["ApprovedPlaylistListPlaylistAssoc"]]:
        return relationship(cascade="all, delete-orphan")

    @declared_attr
    def playlists(cls) -> Mapped[List["Playlist"]]:
        return relationship(
            "Playlist", secondary="approved_playlist_list_playlist_assoc", viewonly=True
        )


class ApprovedPlaylistListSync(CustomSyncBase, ApprovedPlaylistListMixin):
    pass


class ApprovedPlaylistList(CustomBase, ApprovedPlaylistListMixin):
    pass


class ApprovedPlaylistListPlaylistAssocMixin(TimeStampMixin):
    approved_playlist_list_id: Mapped[int] = mapped_column(
        ForeignKey("approved_playlist_list.id"), primary_key=True, nullable=False
    )
    playlist_id: Mapped[int] = mapped_column(
        ForeignKey("playlist.id"), primary_key=True, nullable=False
    )


class ApprovedPlaylistListPlaylistAssocSync(CustomSyncBase, ApprovedPlaylistListPlaylistAssocMixin):
    pass


class ApprovedPlaylistListPlaylistAssoc(CustomBase, ApprovedPlaylistListPlaylistAssocMixin):
    pass
