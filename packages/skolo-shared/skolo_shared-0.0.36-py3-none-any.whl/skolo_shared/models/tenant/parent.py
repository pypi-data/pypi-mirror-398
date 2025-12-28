from sqlalchemy import Column, String, Enum, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..common import AuditModel
from ..common import AuditUserModel, RelationshipEnum, GenderEnum

# Association table for many-to-many relationship between Parent and Student
parent_student_association = Table(
    'parent_student_association',
    AuditModel.metadata,
    Column('parent_id', UUID(as_uuid=True), ForeignKey('parents.id'), primary_key=True),
    Column('student_id', UUID(as_uuid=True), ForeignKey('students.id'), primary_key=True),
    Column('relationship_to_student', Enum(RelationshipEnum))
)


class Parent(AuditUserModel):
    __tablename__ = 'parents'
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True)
    phone_number = Column(String(20), index=True)
    address = Column(String(255))
    gender = Column(Enum(GenderEnum))
    occupation = Column(String(255))
    students = relationship("Student", secondary=parent_student_association, back_populates="parents")
