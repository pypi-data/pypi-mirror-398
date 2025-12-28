from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..common import AuditModel


class ExpenditureCategory(AuditModel):
    """
    Model for categorizing school expenditures (e.g., Salaries, Utilities, Maintenance).
    """
    __tablename__ = 'expenditure_categories'

    category_name = Column(String(255), unique=True, nullable=False)
    description = Column(String(255))

    # Relationship to SchoolExpenditure: One category can have many expenditures
    expenditures = relationship("SchoolExpenditure", back_populates="category")


class SchoolExpenditure(AuditModel):
    """
    Model for tracking school expenditures.
    """
    __tablename__ = 'school_expenditures'

    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(String(500))
    expenditure_date = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Foreign key to ExpenditureCategory
    expenditure_category_id = Column(UUID(as_uuid=True), ForeignKey('expenditure_categories.id'), nullable=False)
    # Foreign key to AcademicYears (to link expenditure to a specific academic period)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id'), nullable=False)

    # Relationships
    category = relationship("ExpenditureCategory", back_populates="expenditures")
    academic_year = relationship("AcademicYears")  # Assuming AcademicYears model exists and is imported
