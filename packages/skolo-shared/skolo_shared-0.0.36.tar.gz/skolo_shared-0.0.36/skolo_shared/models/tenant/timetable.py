from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship

from ..common import AuditModel


class AcademicYears(AuditModel):
    """
    Academic year model.
    """
    __tablename__ = 'academic_years'
    year_name = Column(String(255), nullable=False, unique=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    student_facility_mappings = relationship("StudentFacilityMapping", back_populates="academic_year")
    attendances = relationship("StudentAttendance", back_populates="academic_year")
    holidays = relationship("SchoolHoliday", back_populates="academic_year")

