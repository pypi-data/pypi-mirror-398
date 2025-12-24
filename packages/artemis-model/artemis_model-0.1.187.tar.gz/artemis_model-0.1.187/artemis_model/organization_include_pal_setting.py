import uuid
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declared_attr

from artemis_model.base import TimeStampMixin, CustomSyncBase, CustomBase


class OrganizationIncludePalSettingMixin(TimeStampMixin):
    """Organization-level setting for including parental advisory (explicit) content."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, index=True
    )
    include_pal: Mapped[bool] = mapped_column(nullable=False, default=False)

    @declared_attr
    def organization(cls) -> Mapped["Organization"]:
        return relationship(back_populates="include_pal_setting")

    __table_args__ = (
        UniqueConstraint("organization_id", name="unique_organization_include_pal_setting"),
    )


class OrganizationIncludePalSettingSync(CustomSyncBase, OrganizationIncludePalSettingMixin):
    pass


class OrganizationIncludePalSetting(CustomBase, OrganizationIncludePalSettingMixin):
    pass
