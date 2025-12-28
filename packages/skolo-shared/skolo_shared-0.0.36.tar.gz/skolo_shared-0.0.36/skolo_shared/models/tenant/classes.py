# classes.py
from sqlalchemy import Column, String, ForeignKey, UUID
from sqlalchemy.orm import relationship

from .events import event_news_classes
from ..common import AuditModel


class Classes(AuditModel):
    """
    Class model.
    """
    __tablename__ = 'classes'
    class_name = Column(String(255), nullable=False)
    # Add relationship to Student
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"))
    students = relationship("Student", back_populates="cls")
    # Add relationship to StudentFacilityMapping
    student_facility_mappings = relationship("StudentFacilityMapping", back_populates="cls")
    # Add relationship to Fee
    fees = relationship("Fee", back_populates="cls")
    # Add relationship to Section
    sections = relationship("Section", back_populates="class_")

    # Use explicit primary to ensure proper schema mapping
    attendances = relationship(
        "StudentAttendance",
        back_populates="class_relation",
        primaryjoin="Classes.id == StudentAttendance.class_id",
        foreign_keys="StudentAttendance.class_id"
    )
    events_news = relationship(
        "EventNews",
        secondary=event_news_classes,
        back_populates="target_classes"
    )


class Section(AuditModel):
    __tablename__ = "sections"
    name = Column(String, index=True)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    # Add relationship to Class
    class_ = relationship("Classes", back_populates="sections")
    # Add relationship to Student
    students = relationship("Student", back_populates="section")

    # Also use deferred evaluation for the section relationship
    attendances = relationship(
        "StudentAttendance",
        back_populates="section",
        primaryjoin="Section.id == StudentAttendance.section_id",
        foreign_keys="StudentAttendance.section_id"
    )
    events_news = relationship("EventNews", secondary="event_news_sections", back_populates="target_sections")
