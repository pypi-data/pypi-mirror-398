import uuid

from sqlalchemy import Column, Numeric, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..common import AuditModel, Base, PaymentMethodEnum


class StudentPayment(AuditModel):
    """
    Student payment record.
    """
    __tablename__ = 'student_payments'
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), nullable=False)
    payment_date = Column(DateTime(timezone=True), default=func.now())
    amount = Column(Numeric(10, 2), nullable=False)  # Total payment amount
    payment_method = Column(Enum(PaymentMethodEnum), nullable=False)
    description = Column(String(255))
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id'), nullable=False)
    # Add relationship to Student
    student = relationship("Student")
    # Add relationship to AcademicYear
    academic_year = relationship("AcademicYears")
    # Add relationship to StudentPaymentsFeesMapping
    fees_mapping = relationship("StudentPaymentsFeesMapping", back_populates="student_payment")
    is_waived = Column(Boolean, nullable=False, server_default="false")


class StudentPaymentsFeesMapping(Base):
    """
    Mapping between student payments and the fee_category they cover.
    """
    __tablename__ = 'student_payments_fees_mapping'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Add an ID
    # student_payment_id = Column(Integer, ForeignKey('student_payments.id'), nullable=False) # Changed to UUID
    student_payment_id = Column(UUID(as_uuid=True), ForeignKey('student_payments.id'), nullable=False)
    # student_fixed_fee_id = Column(Integer, ForeignKey('student_fixed_fees.id'), nullable=False) # Changed to UUID
    student_fixed_fee_id = Column(UUID(as_uuid=True), ForeignKey('student_fixed_fees.id'), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)  # Amount paid for this fee
    # Add relationship to StudentPayment
    student_payment = relationship("StudentPayment", back_populates="fees_mapping")
    # Add relationship to StudentFixedFee
    student_fixed_fee = relationship("StudentFixedFee")
