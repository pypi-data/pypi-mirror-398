# skolo_shared/models/staff.py

import enum
from sqlalchemy import Column, String, Enum, ForeignKey, DateTime, Numeric, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..common import AuditModel, AttendanceStatus, PresentTypeEnum, DeviceTypeEnum

from ..common import SalaryMonthEnum, StaffTypeEnum, CTCComponentTypeEnum
from sqlalchemy import (
    Index,
    CheckConstraint,
    UniqueConstraint,
    Integer,
)
from sqlalchemy.sql import text


class Staff(AuditModel):
    """
    Staff model for both teaching and non-teaching personnel.
    """
    __tablename__ = 'staff'
    __table_args__ = (
        Index("idx_staff_status", "status"),
    )
    # ✅ AUTO-GENERATED STAFF CODE
    staff_code = Column(
        String(50),
        nullable=False,
        unique=True,
        server_default=text(
            "'STF-' || nextval('staff_code_seq')"
        )
    )
    name = Column(String(255), nullable=False)
    staff_type = Column(Enum(StaffTypeEnum), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone_number = Column(String(20))
    address = Column(String(255))
    date_of_joining = Column(DateTime(timezone=True), nullable=False)
    date_of_termination = Column(DateTime(timezone=True), nullable=True)  # Nullable for active staff
    qualification = Column(String(255))  # e.g., "Bachelor's in Education", "MBA"

    # Relationships
    ctc_structures = relationship("StaffCTCStructure", back_populates="staff", cascade="all, delete-orphan")
    payments = relationship("StaffPaymentRecord", back_populates="staff", cascade="all, delete-orphan")

    # Add relationship to StudentAttendance
    marked_attendances = relationship(
        "StudentAttendance",
        back_populates="teacher",
        primaryjoin="Staff.id == StudentAttendance.marked_by",
        foreign_keys="StudentAttendance.marked_by"
    )

    # Add relationship to SubjectTeacherMappings
    subject_links = relationship("SubjectTeacherMappings", back_populates="teacher")  # Link to SubjectTeacherMappings
    attendances = relationship("StaffAttendance", back_populates="staff", cascade="all, delete-orphan")


class StaffCTCStructure(AuditModel):
    """
    Represents the Cost-to-Company (CTC) structure for a staff member.
    """
    __tablename__ = 'staff_ctc_structures'
    __table_args__ = (
        # Prevent invalid salary values
        CheckConstraint("total_ctc > 0", name="chk_ctc_positive"),

        # Only ONE ACTIVE CTC per staff
        Index(
            "uq_active_ctc_per_staff",
            "staff_id",
            unique=True,
            postgresql_where=text(
                "status = 'ACTIVE' AND deleted_at IS NULL"
            ),
        ),

        Index("idx_ctc_staff", "staff_id"),
    )

    staff_id = Column(UUID(as_uuid=True), ForeignKey('staff.id'), nullable=False)
    total_ctc = Column(Numeric(10, 2), nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)  # Null means current
    # Relationships
    components = relationship("StaffCTCComponent", back_populates="ctc_structure", cascade="all, delete-orphan")
    staff = relationship("Staff", back_populates="ctc_structures")


class StaffCTCComponent(AuditModel):
    """
    Represents individual components of a CTC structure.
    """
    __tablename__ = 'staff_ctc_components'
    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_component_amount"),

        # Same component name cannot repeat in same CTC
        UniqueConstraint(
            "ctc_structure_id",
            "name",
            name="uq_component_per_ctc"
        ),
    )

    ctc_structure_id = Column(UUID(as_uuid=True), ForeignKey('staff_ctc_structures.id'), nullable=False)
    name = Column(String(100), nullable=False)  # e.g., "Basic", "HRA", "Travel Allowance", "PF"
    amount = Column(Numeric(10, 2), nullable=False)  # Amount for this component monthly
    component_type = Column(Enum(CTCComponentTypeEnum), nullable=False)  # ALLOWANCE, DEDUCTION, BONUS, etc.
    ctc_structure = relationship("StaffCTCStructure", back_populates="components")


class StaffPaymentRecord(AuditModel):
    """
    Tracks salary payments for staff members.
    """
    __tablename__ = 'staff_payment_records'
    __table_args__ = (
        CheckConstraint("total_paid > 0", name="chk_payment_positive"),

        # Prevent duplicate payment per month
        Index(
            "uq_staff_salary_month",
            "staff_id",
            "salary_month",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    staff_id = Column(UUID(as_uuid=True), ForeignKey('staff.id'), nullable=False)
    ctc_structure_id = Column(UUID(as_uuid=True), ForeignKey('staff_ctc_structures.id'), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id'), nullable=False)
    salary_month = Column(Enum(SalaryMonthEnum), nullable=False)
    payment_date = Column(DateTime(timezone=True), default=func.now())
    total_paid = Column(Numeric(10, 2), nullable=False)  # Total amount paid in this record
    is_partial = Column(Boolean, default=False)  # Indicates if the payment is partial
    description = Column(String(255))  # Optional description for the payment

    # Relationships
    payment_breakdown = relationship("StaffPaymentBreakdown", back_populates="payment_record",
                                     cascade="all, delete-orphan")
    staff = relationship("Staff", back_populates="payments")


class StaffPaymentBreakdown(AuditModel):
    """
    Represents the breakdown of a payment into individual CTC components.
    """
    __tablename__ = 'staff_payment_breakdowns'
    __table_args__ = (
        CheckConstraint("amount_paid >= 0", name="chk_paid_positive"),

        # Same component cannot repeat in a single payment
        UniqueConstraint(
            "payment_record_id",
            "ctc_component_id",
            name="uq_component_once_per_payment"
        ),
    )

    payment_record_id = Column(UUID(as_uuid=True), ForeignKey('staff_payment_records.id'), nullable=False)
    ctc_component_id = Column(UUID(as_uuid=True), ForeignKey('staff_ctc_components.id'),
                              nullable=False)  # Reference to specific CTC component
    amount_paid = Column(Numeric(10, 2), nullable=False)  # Amount paid for this component
    payment_record = relationship("StaffPaymentRecord", back_populates="payment_breakdown")


class StaffAttendance(AuditModel):
    """
    Stores attendance records for staff members, including location and selfie.
    """
    __tablename__ = 'staff_attendance'

    staff_id = Column(UUID(as_uuid=True), ForeignKey('staff.id'), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=func.now())
    is_present = Column(Boolean, default=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    selfie_url = Column(String(512), nullable=True)
    location_verified = Column(Boolean, default=False)  # Whether geolocation check passed
    device_id = Column(String(255), nullable=True)  # Optional device tracking
    device_type = Column(Enum(DeviceTypeEnum), nullable=True,
                         default=DeviceTypeEnum.MOBILE)  # e.g., "Mobile", "Desktop"
    approved_by = Column(UUID(as_uuid=True), ForeignKey('public.users.id'),
                         nullable=True)  # Who approved the attendance if its not self-marked or not gelocation verified
    remarks = Column(String(255), nullable=True)

    staff = relationship("Staff", back_populates="attendances")
