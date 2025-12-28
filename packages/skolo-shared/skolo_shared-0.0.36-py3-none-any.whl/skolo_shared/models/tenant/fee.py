from ..common import AuditModel, PaymentStatusEnum
import uuid

from sqlalchemy import Column, Numeric, ForeignKey, Enum, DateTime, Computed, event, select
from sqlalchemy import String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class FeeCategory(AuditModel):
    """
    Fee category model.
    """
    __tablename__ = 'fee_categories'
    category_name = Column(String(255), nullable=False)
    payment_schedule = Column(Integer, nullable=False)
    is_optional = Column(Boolean, default=False)
    is_class_specific_fee = Column(Boolean, default=False)
    core_fee = Column(Boolean, default=False, nullable=False)  # Indicates if this is a core fee like TUITION or
    # DAY_BOARDING
    educational_supplies = Column(Boolean, default=False, nullable=False)  # Indicates if this fee is for educational
    # supplies like BOOKS EXERCISE BOOKS DRESS
    # Relationship to Fee: A FeeCategory has many Fees
    fees = relationship("Fee", back_populates="fee_category")
    # Relationship to StudentFixedFee: A FeeCategory has many StudentFixedFees
    student_fixed_fees = relationship("StudentFixedFee", back_populates="fee_category")
    student_facility_mappings = relationship("StudentFacilityMapping", back_populates="fee_category")


class ConcessionType(AuditModel):
    """
    Concession type model.
    """
    __tablename__ = 'concession_types'
    concession_name = Column(String(255), nullable=False)
    description = Column(String(255))
    # Relationship to StudentFixedFee: A ConcessionType has many StudentFixedFees
    student_fixed_fees = relationship("StudentFixedFee", back_populates="concession_type")


class Fee(AuditModel):
    """
    Fee model. Defines individual fee entries that belong to a category, class, and academic year.
    """
    __tablename__ = 'fees'  # Changed to 'fees' (plural)

    fee_category_id = Column(UUID(as_uuid=True), ForeignKey('fee_categories.id'), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey('classes.id'), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(String(255))
    payment_schedule = Column(Integer, nullable=False)
    is_optional = Column(Boolean, default=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id'), nullable=False)
    # Relationship to FeeCategory: A Fee belongs to one FeeCategory
    fee_category = relationship("FeeCategory", back_populates="fees")

    # Relationship to Class: A Fee belongs to one Class
    # You will need to define the 'Classes' model and its back_populates
    cls = relationship("Classes", back_populates="fees")  # Assuming Classes model has 'fees' relationship

    # Relationship to AcademicYear: A Fee belongs to one AcademicYear
    academic_year = relationship("AcademicYears")  # Assuming AcademicYears model exists
    transport_route_fee_mappings = relationship("TransportRouteFeeMapping", back_populates="fee")


class StudentFixedFee(AuditModel):
    """
    Student-specific fee, including concessions for each student with specified categories.
    Multiple entries of a single student can be possible.
    includes both core fees and the school supplies as we are maintaining the total service/supplies taken by a student
    ie. admission ,tuition ,books ,dress
    having only one entry for each categories for  a student
    """
    __tablename__ = 'student_fixed_fees'
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), nullable=False)
    fee_category_id = Column(UUID(as_uuid=True), ForeignKey('fee_categories.id'), nullable=False)
    fee_id = Column(UUID(as_uuid=True), ForeignKey('fees.id'), nullable=False)
    concession_type_id = Column(UUID(as_uuid=True), ForeignKey('concession_types.id'))
    concession_amount = Column(Numeric(10, 2), default=0.00)
    amount = Column(Numeric(10, 2), nullable=False)  # Amount after concession
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id'), nullable=False)
    # Add relationship to Student
    student = relationship("Student", back_populates="fixed_fees")
    # Add relationship to FeeCategory
    fee_category = relationship("FeeCategory", back_populates="student_fixed_fees")
    # Add relationship to Fee
    # This relationship doesn't need a back_populates if 'Fee' doesn't explicitly link back here
    # If 'Fee' should have a relationship to 'StudentFixedFee', you'd add it there.
    fee = relationship("Fee")  # The 'fee' object it's associated with

    # Add relationship to ConcessionType
    # This relationship doesn't need a back_populates if 'ConcessionType' doesn't explicitly link back here
    concession_type = relationship("ConcessionType")

    # Add relationship to AcademicYear
    academic_year = relationship("AcademicYears")
    # New relationship for payment schedule mappings
    payment_schedule_mappings = relationship(
        "StudentFixedFeePaymentScheduleMapping",
        back_populates="student_fixed_fee",
        cascade="all, delete-orphan"  # This will delete mappings if the fixed fee is deleted
    )
    facility_mappings = relationship("StudentFacilityMapping", back_populates="student_fixed_fee")


class StudentFixedFeePaymentScheduleMapping(AuditModel):
    """
    Maps student fixed fees to their payment schedules.
    Each entry represents a single payment installment for a student's fixed fee.
    pending_amount is managed by the database, payment_status by ORM event.
    """
    __tablename__ = 'student_fixed_fee_payment_schedule_mappings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), nullable=False)
    student_fixed_fee_id = Column(UUID(as_uuid=True), ForeignKey('student_fixed_fees.id'), nullable=False)
    fee_id = Column(UUID(as_uuid=True), ForeignKey('fees.id'), nullable=False)

    # The actual amount expected for this specific installment
    amount_to_be_paid = Column(Numeric(10, 2), nullable=False)

    payment_due_date = Column(DateTime(timezone=True), server_default=func.now())
    paid_date = Column(DateTime(timezone=True))
    paid_amount = Column(Numeric(10, 2), default=0.00)
    waiver_amount = Column(Numeric(10, 2), default=0.00)

    # pending_amount is a GENERATED ALWAYS AS STORED column in the database
    pending_amount = Column(
        Numeric(10, 2),
        Computed(
            "GREATEST(amount_to_be_paid - paid_amount - waiver_amount, 0.00)",
            persisted=True
        ),
        nullable=False
    )

    # payment_status is a regular column, managed by ORM events
    payment_status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING, nullable=False)

    # Relationships
    student = relationship("Student")
    student_fixed_fee = relationship("StudentFixedFee", back_populates="payment_schedule_mappings")
    fee = relationship("Fee")


@event.listens_for(StudentFixedFeePaymentScheduleMapping, 'before_insert')
@event.listens_for(StudentFixedFeePaymentScheduleMapping, 'before_update')
def update_payment_status(mapper, connection, target):

    current_pending = (
        target.amount_to_be_paid
        - target.paid_amount
        - target.waiver_amount
    )
    current_pending = max(0, current_pending)

    # ✅ get DB time WITH timezone (UTC)
    db_now = connection.execute(select(func.now())).scalar()

    if current_pending <= 0:
        target.payment_status = PaymentStatusEnum.PAID
        if not target.paid_date:
            target.paid_date = db_now

    elif target.payment_due_date and target.payment_due_date < db_now:
        target.payment_status = PaymentStatusEnum.OVERDUE

    else:
        target.payment_status = PaymentStatusEnum.PENDING
