import enum
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, List

from sqlalchemy import JSON, DateTime, Index, Integer, String, Text
from sqlalchemy import JSON as SA_JSON
from sqlalchemy import Enum as SA_Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from nlbone.adapters.db.postgres.base import Base
from nlbone.utils.time import now

try:
    from sqlalchemy.dialects.postgresql import JSONB, UUID

    JSONType = JSONB
    UUIDType = UUID(as_uuid=True)
except Exception:
    JSONType = SA_JSON
    UUIDType = String(36)


@dataclass
class CurrentUserData:
    active: bool
    id: int
    email: str
    exp: int
    iat: int
    preferred_username: str
    name: str
    phone_number: str
    verifications: List[str]
    allowed_permissions: List[str]

    @classmethod
    def from_dict(cls, data: dict) -> "CurrentUserData":
        return cls(
            active=data.get("active"),
            id=data.get("sub"),
            email=data.get("email"),
            exp=data.get("exp"),
            iat=data.get("iat"),
            preferred_username=data.get("preferred_username"),
            name=data.get("name"),
            phone_number=data.get("phone_number"),
            verifications=data.get("verifications", []),
            allowed_permissions=data.get("allowed_permissions", []),
        )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    entity: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    operation: Mapped[str] = mapped_column(String(10), nullable=False)  # INSERT/UPDATE/DELETE
    changes: Mapped[dict | None] = mapped_column(JSONType, nullable=True)

    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_audit_entity_entityid", "entity", "entity_id"),
        Index("ix_audit_created_at", "created_at"),
    )


class OutboxStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"


class Outbox(Base):
    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    headers: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    key: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    status: Mapped[OutboxStatus] = mapped_column(SA_Enum(OutboxStatus), default=OutboxStatus.PENDING, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    def mark_failed(self, error: str, *, backoff: timedelta = timedelta(seconds=30)):
        self.status = OutboxStatus.FAILED
        self.last_error = error
        self.next_attempt_at = now() + backoff
        self.attempts += 1

    def mark_published(self):
        self.status = OutboxStatus.PUBLISHED
        self.next_attempt_at = None


def to_outbox_row(evt) -> Outbox:
    return Outbox(topic=evt.topic, payload=evt.__dict__)
