import enum

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PropertyType(str, enum.Enum):
    rumah = "rumah"
    apartemen = "apartemen"
    kavling = "kavling"
    ruko = "ruko"
    tanah = "tanah"


class ListingType(str, enum.Enum):
    dijual = "dijual"
    disewa = "disewa"


class LeadStatus(str, enum.Enum):
    new = "new"
    contacted = "contacted"
    appointment = "appointment"
    showing = "showing"
    negotiation = "negotiation"
    closed_won = "closed_won"
    closed_lost = "closed_lost"


class LeadSource(str, enum.Enum):
    manual = "manual"
    whatsapp = "whatsapp"
    web = "web"


class UserRole(str, enum.Enum):
    admin = "admin"
    agent = "agent"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default="agent")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    @property
    def email(self) -> str | None:
        if not self.username:
            return None
        return f"{self.username}@livininbintaro.my.id"


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True)
    description = Column(Text)
    property_type = Column(String(20))
    listing_type = Column(String(20))
    price = Column(BigInteger)
    price_label = Column(String(50))
    area_location = Column(String(100))
    cluster = Column(String(100))
    sektor = Column(String(50))
    address = Column(String(255))
    block = Column(String(20))
    block_no = Column(String(20))
    bedrooms = Column(Integer)
    bedrooms_extra = Column(Integer, default=0)
    bathrooms = Column(Integer)
    bathrooms_extra = Column(Integer, default=0)
    land_area = Column(Integer)
    building_area = Column(Integer)
    floors = Column(Integer)
    certificate = Column(String(20))
    electricity = Column(String(20))
    cpa_code = Column(String(30), index=True)
    cpa_expiry = Column(String(20))
    images = Column(JSON, default=[])
    drive_folder_id = Column(String(255))
    drive_link = Column(Text)
    summary_client = Column(Text)
    summary_ma = Column(Text)
    is_hot = Column(Boolean, default=False)
    hot_reason = Column(String(50))
    hot_note = Column(Text)
    hot_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    source = Column(String(20), default="manual")
    requirement_text = Column(Text)
    budget_min = Column(BigInteger)
    budget_max = Column(BigInteger)
    preferred_type = Column(String(20))
    preferred_area = Column(String(100))
    status = Column(String(20), default="new")
    assigned_to = Column(Integer, ForeignKey("users.id"))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    bucket = Column(String(20), default="inbox", index=True)
    ai_score = Column(Integer, nullable=True)
    ai_score_reason = Column(Text, nullable=True)
    ai_scored_at = Column(DateTime, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_summary_at = Column(DateTime, nullable=True)
    last_contacted_at = Column(DateTime, nullable=True)
    next_follow_up_at = Column(DateTime, nullable=True)
    welcome_sent = Column(Boolean, default=False)
    follow_up_d1_sent = Column(Boolean, default=False)
    follow_up_d7_sent = Column(Boolean, default=False)
    follow_up_d14_sent = Column(Boolean, default=False)
    follow_up_reason = Column(Text, nullable=True)


class LeadActivity(Base):
    __tablename__ = "lead_activities"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    activity_type = Column(String(30))
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LeadNote(Base):
    __tablename__ = "lead_notes"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    content = Column(Text, nullable=False)
    note_type = Column(String(20), default="manual")
    created_at = Column(DateTime, default=func.now())


class WAMessage(Base):
    __tablename__ = "wa_messages"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(
        Integer, ForeignKey("leads.id", ondelete="SET NULL"), nullable=True
    )
    phone = Column(String(20), nullable=False, index=True)
    sender_name = Column(String(100), nullable=True)
    message = Column(Text, nullable=True)
    direction = Column(String(10), nullable=False, default="inbound")
    message_type = Column(String(20), default="text")
    media_url = Column(Text, nullable=True)
    fonnte_message_id = Column(String(100), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    lead = relationship("Lead", backref="wa_messages")


class WATemplate(Base):
    __tablename__ = "wa_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    trigger_type = Column(String(30), nullable=False)
    message_template = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class ContentCalendar(Base):
    __tablename__ = "content_calendar"

    id = Column(Integer, primary_key=True, index=True)
    post_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    scheduled_date = Column(Date, nullable=True)
    status = Column(String(20), default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
