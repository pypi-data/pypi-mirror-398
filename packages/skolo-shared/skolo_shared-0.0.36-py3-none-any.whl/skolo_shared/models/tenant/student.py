from ..common import AuditModel, GenderEnum, StudentStatusEnum

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .parent import parent_student_association


# TODO remove this table
class StudentFacilityTypes(AuditModel):
    """
   Student Status type model
    """
    __tablename__ = 'student_facility_types'
    facility_type_name = Column(String(255), unique=True, nullable=False)
    description = Column(String)


class StudentFacilityMapping(AuditModel):
    """
    Maps students to the facilities or services they are enrolled in (e.g., tuition, day boarding, transport,
    Admission also as we will have all the start and end date).
    Which user can have what to look a status for later usage
    only using this table when the fess is a core fee not a school supplies like book or dress
    """
    __tablename__ = 'student_facility_mapping'
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey('classes.id'), nullable=False)
    fee_category_id = Column(UUID(as_uuid=True), ForeignKey('fee_categories.id'), nullable=False)
    student_fixed_fee_id = Column(UUID(as_uuid=True), ForeignKey('student_fixed_fees.id'))
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True))
    payment_schedule = Column(Integer, nullable=False, default=0)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id'), nullable=False)
    # Add relationship to Student
    student = relationship("Student", back_populates="student_facility_mappings")
    cls = relationship("Classes", back_populates="student_facility_mappings")
    academic_year = relationship("AcademicYears", back_populates="student_facility_mappings")
    fee_category = relationship("FeeCategory", back_populates="student_facility_mappings")
    transport_assignments = relationship("StudentTransportAssignment", back_populates="student_facility_mapping")
    student_fixed_fee = relationship("StudentFixedFee", back_populates="facility_mappings")


class Student(AuditModel):
    """
    Student model.
    """
    __tablename__ = 'students'
    name = Column(String, index=True)
    roll_number = Column(String, index=True)
    date_of_birth = Column(DateTime(timezone=True))
    enrolment_date = Column(DateTime(timezone=True))
    gender = Column(Enum(GenderEnum))
    email = Column(String(255), unique=True)
    phone_number = Column(String(20))
    address = Column(String(255))
    class_id = Column(UUID(as_uuid=True), ForeignKey('classes.id'), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"))
    medical_history = Column(String(255))
    blood_group = Column(String(10))
    emergency_contact_number = Column(String(20))
    old_school_name = Column(String(255))
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id'), nullable=False)
    # Override status with StudentStatusEnum
    status = Column(Enum(StudentStatusEnum), default=StudentStatusEnum.ACTIVE)
    # Add relationship to Class
    cls = relationship("Classes", back_populates="students")
    # Add relationship to StudentFacilityMapping
    student_facility_mappings = relationship("StudentFacilityMapping", back_populates="student")
    # Add relationship to StudentTransportAssignment
    # transport_assignments = relationship("StudentTransportAssignment", back_populates="student")
    # Add relationship to StudentFixedFees
    fixed_fees = relationship("StudentFixedFee", back_populates="student")
    # Add relationship to Section
    section = relationship("Section", back_populates="students")
    attendances = relationship("StudentAttendance", back_populates="student")
    # Add relationship to ParentStudentAssociation
    parents = relationship("Parent", secondary=parent_student_association, back_populates="students")

    # This gives access to transport assignments via student_facility_mappings
    @property
    def transport_assignments(self):
        return [ta for sfm in self.student_facility_mappings for ta in sfm.transport_assignments]
