"""Auth models."""

from enum import Enum
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import UUID, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declared_attr

from artemis_model.base import AuditMixin, CustomSyncBase, TimeStampMixin, CustomBase


class UserUnverifiedAccountMixin(TimeStampMixin):
    """
    This table is used to store the account info of users who have requested an account but have not yet
    been verified. Once the user has been verified, the account will be moved to the UserAccount table.
    """

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    mobile: Mapped[str] = mapped_column(nullable=True, index=True)
    is_root_user: Mapped[bool] = mapped_column(default=True)
    is_email_verified: Mapped[bool] = mapped_column(default=False)
    is_mobile_verified: Mapped[bool] = mapped_column(default=False)
    is_onboarded: Mapped[bool] = mapped_column(default=False)
    password = mapped_column(LargeBinary, nullable=False)
    provider: Mapped[str] = mapped_column(default="internal")


class UserUnverifiedAccountSync(CustomSyncBase, UserUnverifiedAccountMixin):
    pass


class UserUnverifiedAccount(CustomBase, UserUnverifiedAccountMixin):
    pass


class UserAccountMixin(TimeStampMixin):
    """
    This table is used to store the account info of users who have been verified.
    """

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(index=True, unique=True)
    name: Mapped[str] = mapped_column(nullable=False)
    mobile: Mapped[Optional[str]] = mapped_column(nullable=True, unique=True, index=True)
    password = mapped_column(LargeBinary, nullable=True)
    provider: Mapped[str] = mapped_column(nullable=False)
    oauth_id: Mapped[Optional[str]] = mapped_column(nullable=True, index=True)
    image_url: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_email_verified: Mapped[bool] = mapped_column(default=False)
    is_mobile_verified: Mapped[bool] = mapped_column(default=False)
    is_root_user: Mapped[bool] = mapped_column(default=True)
    is_super_admin: Mapped[bool] = mapped_column(default=False)
    disabled: Mapped[bool] = mapped_column(default=False)
    disabled_reason: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_onboarded: Mapped[bool] = mapped_column(default=False)

    @declared_attr
    def login_histories(cls) -> Mapped["LoginHistory"]:
        return relationship("LoginHistory", back_populates="account")

    @declared_attr
    def user(cls) -> Mapped["User"]:
        return relationship("User", back_populates="account")


class UserAccountSync(CustomSyncBase, UserAccountMixin):
    pass


class UserAccount(CustomBase, UserAccountMixin):
    pass


class LoginHistoryMixin:
    """
    This table is used to store the login history of users.
    """

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_account.id"), nullable=False, index=True
    )
    ip_address: Mapped[str] = mapped_column(nullable=True)
    created_at = mapped_column(DateTime, default=datetime.utcnow)

    @declared_attr
    def account(cls) -> Mapped["UserAccount"]:
        return relationship("UserAccount", back_populates="login_histories")


class LoginHistorySync(CustomSyncBase, LoginHistoryMixin):
    pass


class LoginHistory(CustomBase, LoginHistoryMixin):
    pass


class OAuthCsrfStateMixin(TimeStampMixin):
    id: Mapped[str] = mapped_column(primary_key=True, unique=True)
    client_base_url: Mapped[str] = mapped_column(nullable=True)


class OAuthCsrfStateSync(CustomSyncBase, OAuthCsrfStateMixin):
    pass


class OAuthCsrfState(CustomBase, OAuthCsrfStateMixin):
    pass


class OrionWebplayerCodeMixin(TimeStampMixin, AuditMixin):
    """Orion webplayer code mixin."""

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code_hash: Mapped[str] = mapped_column(
        unique=True, nullable=False
    )  # Argon2id of normalized code
    name: Mapped[str] = mapped_column(nullable=False)
    zone_id: Mapped[int] = mapped_column(nullable=False, index=True)


class OrionWebplayerCodeSync(CustomSyncBase, OrionWebplayerCodeMixin):
    pass


class OrionWebplayerCode(CustomBase, OrionWebplayerCodeMixin):
    pass


class PlayerRefreshTokenMixin(TimeStampMixin):
    """
    Refresh token for Player.
    We look up by token_id (PK), then verify `secret` against `secret_hash`.
    """

    # this is the public part we send to the client
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    code_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orion_webplayer_code.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    # store zone_id too (helps auth decisions / debugging)
    zone_id: Mapped[Optional[int]] = mapped_column(index=True)

    # bcrypt/argon2 hash of the secret part
    secret_hash: Mapped[str] = mapped_column(nullable=False)
    is_suspended: Mapped[bool] = mapped_column(default=False)


class PlayerRefreshTokenSync(CustomSyncBase, PlayerRefreshTokenMixin):
    pass


class PlayerRefreshToken(CustomBase, PlayerRefreshTokenMixin):
    pass


class Scope(str, Enum):
    """Scope enum."""

    PLAYER = "player"
    MANAGE = "manage"


class TokenData(BaseModel):
    """Token data."""

    account_id: uuid.UUID
    user_id: uuid.UUID
    scope: Scope


class RefreshTokenData(TokenData):
    """Refresh token data."""

    zone_id: int | None = None
    code_id: uuid.UUID | None = None
