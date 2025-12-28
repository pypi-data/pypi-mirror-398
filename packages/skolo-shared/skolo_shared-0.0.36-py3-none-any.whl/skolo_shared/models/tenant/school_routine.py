from ..common import AuditModel, RoutineDayEnum
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, UUID, Time
from sqlalchemy.orm import relationship


class SchoolRoutine(AuditModel):
    """
    Represents the school routine/timetable for a class/section/subject/period/day.

    Flow to create a routine for Monday to Saturday:
    1. For each class and section, iterate through days (MONDAY to SATURDAY).
    2. For each day, define periods (e.g., 1st period, 2nd period, etc.) with start and end times.
    3. For each period, assign a subject and link it to one or more staff (teachers).
    4. Assign priority to staff for substitution or co-teaching (main teacher = priority 1).
    5. Save each SchoolRoutine entry with class_id, section_id, subject_id, day, period_number, start_time, end_time.
    6. For each routine slot, create SchoolRoutineStaff entries for assigned staff, with priority and substitution info.
    7. Repeat for all periods and days for the class/section.
    8. This allows flexible assignment, substitution, and management of routines for the week.
    9. count of columns: 9 + 7 = 16
    """
    __tablename__ = "school_routines"
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    day = Column(Enum(RoutineDayEnum), nullable=False)
    period_number = Column(Integer, nullable=False)  # e.g., 1st period, 2nd period
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    remarks = Column(String(255), nullable=True)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id'), nullable=False)

    # Relationships
    class_ = relationship("Classes", backref="school_routines")
    section = relationship("Section", backref="school_routines")
    subject = relationship("Subject", backref="school_routines")
    staff_assignments = relationship("SchoolRoutineStaff", back_populates="routine", cascade="all, delete-orphan")


class SchoolRoutineStaff(AuditModel):
    """
    Links staff to a routine slot, with priority for substitution/co-teaching.
    count of columns: 6 + 7 = 13
    """
    __tablename__ = "school_routine_staff"
    routine_id = Column(UUID(as_uuid=True), ForeignKey("school_routines.id"), nullable=False)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=False)
    priority = Column(Integer, default=1)  # 1 = main teacher, higher = substitute
    is_substitute = Column(Integer, default=0)  # 0 = main, 1 = substitute
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id'), nullable=False)
    remarks = Column(String(255), nullable=True)

    # Relationships
    routine = relationship("SchoolRoutine", back_populates="staff_assignments")
    staff = relationship("Staff", backref="routine_assignments")
