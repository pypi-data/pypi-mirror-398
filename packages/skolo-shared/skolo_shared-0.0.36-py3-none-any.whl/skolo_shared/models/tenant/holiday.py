from sqlalchemy import Column, String, Date, Boolean, Text, UniqueConstraint, Index, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..common import AuditModel
from ..common.enums import HolidayTypeEnum


class SchoolHoliday(AuditModel):
    """
    Stores school holidays for a particular academic year.

    Fields:
    - academic_year_id: FK to academic_years.id
    - name: short name for the holiday (e.g., "Summer Vacation")
    - start_date / end_date: inclusive date range
    - holiday_type: categorization of the holiday
    - is_recurring: whether this holiday recurs every year (useful for fixed-date holidays)
    - description: optional longer text
    - is_deleted: soft-delete flag

    Indexes and constraints:
    - unique constraint on (academic_year_id, name, start_date) to avoid accidental duplicates
    - index on academic_year_id and start_date/end_date for efficient range queries
    """
    __tablename__ = "school_holidays"
    __table_args__ = (
        UniqueConstraint("academic_year_id", "name", "start_date", name="uq_holiday_academicyear_name_start"),
        Index("ix_holiday_academic_year", "academic_year_id"),
        Index("ix_holiday_start_date", "start_date"),
        Index("ix_holiday_end_date", "end_date"),
    )
    name = Column(String(255), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    holiday_type = Column(SAEnum(HolidayTypeEnum, name="holiday_type_enum"), nullable=False, default=HolidayTypeEnum.SCHOOL_BREAK)
    is_recurring = Column(Boolean, default=False)
    description = Column(Text, nullable=True)

    # Relationship to the AcademicYears model (defined elsewhere in tenant models)
    academic_year = relationship("AcademicYears", back_populates="holidays")

    def __repr__(self):
        return f"<SchoolHoliday(name={self.name}, academic_year_id={self.academic_year_id}, start={self.start_date}, end={self.end_date})>"
