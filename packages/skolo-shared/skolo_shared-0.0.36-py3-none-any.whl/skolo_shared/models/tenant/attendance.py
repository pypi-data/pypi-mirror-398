from ..common import AuditModel, AttendanceStatus, PresentTypeEnum, DeviceTypeEnum

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class StudentAttendance(AuditModel):
    """
    Student attendance model to track daily attendance records.

    Indexes on `attendance_date`, `student_id`, and `class_id` help speed up queries that filter or sort by these fields,
    such as fetching all attendance records for a student, a specific date, or a class.
    """
    __tablename__ = 'student_attendance'
    __table_args__ = (
        UniqueConstraint('student_id', 'attendance_date', name='uq_student_attendance_date'),
        Index('ix_attendance_date', 'attendance_date'),  # Improves queries filtering by attendance_date
        Index('ix_student_id', 'student_id'),  # Improves queries filtering by student_id
        Index('ix_class_id', 'class_id'),  # Improves queries filtering by class_id
    )
    # Foreign keys - explicitly specify the schema for users table
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey('classes.id'), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey('sections.id'), nullable=False)
    # Changed to reference staff.id correctly
    marked_by = Column(UUID(as_uuid=True), ForeignKey('staff.id'), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id'), nullable=False)

    # Attendance details
    attendance_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    status = Column(Enum(AttendanceStatus), nullable=False, default=AttendanceStatus.ABSENT)
    remark = Column(String(255), nullable=True)  # Optional remarks about attendance
    time_in = Column(DateTime(timezone=True), nullable=True)  # For tracking exact entry time
    time_out = Column(DateTime(timezone=True), nullable=True)  # For tracking exit time if needed
    present_type = Column(Enum(PresentTypeEnum), default=PresentTypeEnum.FULL_DAY, nullable=True)
    device_info = Column(Enum(DeviceTypeEnum, default=DeviceTypeEnum.MOBILE, name="device_type_enum"), nullable=True)
    location_info = Column(String(255), nullable=True)

    # For tracking late entries or early departures
    is_late = Column(Boolean, default=False)
    late_reason = Column(String(255), nullable=True)
    # Soft delete flag
    is_deleted = Column(Boolean, default=False)

    # Relationships - ensure proper back references with explicit join conditions
    student = relationship("Student", back_populates="attendances")
    class_relation = relationship("Classes", back_populates="attendances")
    section = relationship("Section", back_populates="attendances")

    # Fixed relationship to Staff with correct join condition
    teacher = relationship(
        "Staff",
        back_populates="marked_attendances",
        primaryjoin="StudentAttendance.marked_by == Staff.id",
        foreign_keys=[marked_by]
    )
    academic_year = relationship("AcademicYears", back_populates="attendances")

    def __repr__(self):
        return f"<StudentAttendance(student_id={self.student_id}, date={self.attendance_date}, status={self.status})>"
