import uuid
from typing import Optional
from datetime import datetime

from sqlalchemy import UUID, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declared_attr

from artemis_model.base import CustomBase, CustomSyncBase, TimeStampMixin


class OrganizationBillingMixin(TimeStampMixin):
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organization.id"), primary_key=True
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(nullable=True, index=True)

    # Single active subscription reference (for org-level billing). When per-location
    # subscriptions are used, this may be null and looked up from OrganizationSubscription.
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(nullable=True, index=True)
    subscription_status: Mapped[Optional[str]] = mapped_column(nullable=True)
    billing_cycle: Mapped[Optional[str]] = mapped_column(nullable=True)
    trial_end: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    current_period_start: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    default_payment_method_id: Mapped[Optional[str]] = mapped_column(nullable=True)

    @declared_attr
    def organization(cls) -> Mapped["Organization"]:
        return relationship("Organization", back_populates="billing", uselist=False)


class OrganizationBilling(CustomBase, OrganizationBillingMixin):
    pass


class OrganizationBillingSync(CustomSyncBase, OrganizationBillingMixin):
    pass


class OrganizationSubscriptionMixin(TimeStampMixin):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organization.id"), index=True
    )
    stripe_subscription_id: Mapped[str] = mapped_column(index=True)
    status: Mapped[Optional[str]] = mapped_column(nullable=True)
    billing_cycle: Mapped[Optional[str]] = mapped_column(nullable=True)
    trial_end: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    current_period_start: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    # Pending cycle change metadata (scheduled to flip at period end)
    pending_billing_cycle: Mapped[Optional[str]] = mapped_column(nullable=True)
    pending_billing_cycle_effective_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    stripe_schedule_id: Mapped[Optional[str]] = mapped_column(nullable=True, index=True)
    # Primary scope for this subscription: 'organization' or 'location'
    scope_type: Mapped[str] = mapped_column(default="organization")
    scope_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    @declared_attr
    def organization(cls) -> Mapped["Organization"]:
        return relationship("Organization", back_populates="subscriptions")

    @declared_attr
    def items(cls) -> Mapped[list["OrganizationSubscriptionItem"]]:
        return relationship(
            "OrganizationSubscriptionItem", back_populates="subscription", cascade="all, delete-orphan"
        )


class OrganizationSubscription(CustomBase, OrganizationSubscriptionMixin):
    pass


class OrganizationSubscriptionSync(CustomSyncBase, OrganizationSubscriptionMixin):
    pass


class OrganizationSubscriptionItemMixin(TimeStampMixin):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organization_subscription.id"), index=True
    )
    stripe_subscription_item_id: Mapped[Optional[str]] = mapped_column(nullable=True, unique=True)
    product_type: Mapped[str] = mapped_column()  # 'location' | 'additional_zone' | ...
    stripe_price_id: Mapped[str] = mapped_column()
    quantity: Mapped[int] = mapped_column()
    scope_type: Mapped[str] = mapped_column(default="organization")  # 'organization' | 'location'
    scope_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, name="metadata", nullable=True)

    @declared_attr
    def subscription(cls) -> Mapped["OrganizationSubscription"]:
        return relationship("OrganizationSubscription", back_populates="items")


class OrganizationSubscriptionItem(CustomBase, OrganizationSubscriptionItemMixin):
    pass


class OrganizationSubscriptionItemSync(CustomSyncBase, OrganizationSubscriptionItemMixin):
    pass


class BillingChangeLogMixin(TimeStampMixin):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    organization_subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    organization_subscription_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    change_type: Mapped[str] = mapped_column()  # e.g., 'subscription_created', 'quantity_updated', 'price_changed'
    old_value_json: Mapped[Optional[dict]] = mapped_column(JSONB, name="old_value", nullable=True)
    new_value_json: Mapped[Optional[dict]] = mapped_column(JSONB, name="new_value", nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(nullable=True)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)


class BillingChangeLog(CustomBase, BillingChangeLogMixin):
    pass


class BillingChangeLogSync(CustomSyncBase, BillingChangeLogMixin):
    pass


class PaymentLogMixin(TimeStampMixin):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    stripe_invoice_id: Mapped[Optional[str]] = mapped_column(nullable=True, index=True)
    amount: Mapped[Optional[int]] = mapped_column(nullable=True)  # cents
    amount_major: Mapped[Optional[float]] = mapped_column(nullable=True)  # dollars (e.g., 18.10)
    currency: Mapped[Optional[str]] = mapped_column(nullable=True)
    status: Mapped[Optional[str]] = mapped_column(nullable=True)  # paid, open, void, uncollectible
    occurred_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    raw: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # webhook payload snapshot
    # One-time payments / checkout tracking
    type: Mapped[Optional[str]] = mapped_column(nullable=True)  # 'subscription_invoice' | 'one_time' | 'checkout'
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(nullable=True, index=True)
    stripe_checkout_session_id: Mapped[Optional[str]] = mapped_column(nullable=True, index=True)


class PaymentLog(CustomBase, PaymentLogMixin):
    pass


class PaymentLogSync(CustomSyncBase, PaymentLogMixin):
    pass


class MusicManageAddonMixin(TimeStampMixin):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope_type: Mapped[str] = mapped_column()  # 'organization' | 'location'
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    active: Mapped[bool] = mapped_column(default=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(default=False)
    quantity: Mapped[int] = mapped_column(default=0)

    stripe_subscription_item_id: Mapped[Optional[str]] = mapped_column(nullable=True, unique=True)
    stripe_price_id: Mapped[Optional[str]] = mapped_column(nullable=True)

    subscription_status: Mapped[Optional[str]] = mapped_column(nullable=True)
    billing_cycle: Mapped[Optional[str]] = mapped_column(nullable=True)
    current_period_start: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class MusicManageAddon(CustomBase, MusicManageAddonMixin):
    pass


class MusicManageAddonSync(CustomSyncBase, MusicManageAddonMixin):
    pass


