from ..common import AuditModel, EventNewsTypeEnum, PriorityEnum, TargetAudienceEnum

from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Boolean, Table, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Association table for many-to-many relationship between events/news and classes
event_news_classes = Table(
    'event_news_classes',
    AuditModel.metadata,
    Column('event_news_id', UUID(as_uuid=True), ForeignKey('events_news.id'), primary_key=True),
    Column('class_id', UUID(as_uuid=True), ForeignKey('classes.id'), primary_key=True)
)

# Association table for many-to-many relationship between events/news and sections
event_news_sections = Table(
    'event_news_sections',
    AuditModel.metadata,
    Column('event_news_id', UUID(as_uuid=True), ForeignKey('events_news.id'), primary_key=True),
    Column('section_id', UUID(as_uuid=True), ForeignKey('sections.id'), primary_key=True)
)


class EventNews(AuditModel):
    """
    Events and News model for school communications
    """
    __tablename__ = 'events_news'

    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    event_news_type = Column(Enum(EventNewsTypeEnum), nullable=False)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.MEDIUM)
    target_audience = Column(Enum(TargetAudienceEnum), nullable=False)

    # Event specific fields
    event_date = Column(DateTime(timezone=True), nullable=True)  # For events
    event_location = Column(String(255), nullable=True)
    registration_required = Column(Boolean, default=False)
    registration_deadline = Column(DateTime(timezone=True), nullable=True)

    # Publishing fields
    publish_date = Column(DateTime(timezone=True), default=func.now())
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    is_published = Column(Boolean, default=False)

    # Academic year context
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id'), nullable=False)

    # Media attachments (optional - can be extended later)

    image_uuids = Column(String(500), nullable=True) #Keeping it String so that we can have multiple image as comma separated in future
    attachment_uuids = Column(String(500), nullable=True) #Keeping it String so that we can have multiple image as comma separated in future


    # Relationships
    academic_year = relationship("AcademicYears")
    target_classes = relationship("Classes", secondary=event_news_classes, back_populates="events_news")
    target_sections = relationship("Section", secondary=event_news_sections, back_populates="events_news")

    # Notifications and read receipts
    notifications = relationship("EventNewsNotification", back_populates="event_news", cascade="all, delete-orphan")
    read_receipts = relationship("EventNewsReadReceipt", back_populates="event_news", cascade="all, delete-orphan")


class EventNewsNotification(AuditModel):
    """
    Tracks notifications sent for events/news
    """
    __tablename__ = 'event_news_notifications'

    event_news_id = Column(UUID(as_uuid=True), ForeignKey('events_news.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('public.users.id'), nullable=False)
    notification_type = Column(String(50), nullable=False)  # EMAIL, SMS, IN_APP
    sent_at = Column(DateTime(timezone=True), default=func.now())
    delivery_status = Column(String(50), default="PENDING")  # PENDING, SENT, DELIVERED, FAILED

    # Relationships
    event_news = relationship("EventNews", back_populates="notifications")


class EventNewsReadReceipt(AuditModel):
    """
    Tracks who has read which events/news
    """
    __tablename__ = 'event_news_read_receipts'

    event_news_id = Column(UUID(as_uuid=True), ForeignKey('events_news.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('public.users.id'), nullable=False)
    read_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    event_news = relationship("EventNews", back_populates="read_receipts")

    # Ensure unique constraint
    __table_args__ = (
        {'schema': None},  # Uses tenant schema
    )


class EventRegistration(AuditModel):
    """
    Handles event registrations when required
    """
    __tablename__ = 'event_registrations'

    event_news_id = Column(UUID(as_uuid=True), ForeignKey('events_news.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('public.users.id'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), nullable=True)  # For parent registrations
    registration_date = Column(DateTime(timezone=True), default=func.now())
    attendance_status = Column(String(50), default="REGISTERED")  # REGISTERED, ATTENDED, ABSENT
    notes = Column(Text, nullable=True)

    # Relationships
    event_news = relationship("EventNews")
    student = relationship("Student")
