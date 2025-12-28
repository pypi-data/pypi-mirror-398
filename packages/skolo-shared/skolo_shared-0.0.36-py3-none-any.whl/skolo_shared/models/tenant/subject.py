from ..common import AuditModel, SubjectCategoryEnum

from sqlalchemy import Column, String, ForeignKey, UUID, DateTime, func, Index, Enum
from sqlalchemy.orm import relationship


class Subject(AuditModel):
    __tablename__ = "subjects"

    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True)

    # Use Enum instead of a foreign key to SubjectCategories
    category = Column(Enum(SubjectCategoryEnum), nullable=False)

    # Optional class-level association
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id'), nullable=False)

    # Relationships
    teachers = relationship("SubjectTeacherMappings", back_populates="subject")
    class_subject_mappings = relationship("ClassSubjectMappings", back_populates="subject")  # Add this relationship

    __table_args__ = (
        Index('idx_subject_code', 'code'),  # Add index for code
        Index('idx_subject_category', 'category'),  # Add index for category
    )


class ClassSubjectMappings(AuditModel):  # Renamed from ClassSubjects
    __tablename__ = "class_subject_mappings"

    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"),
                        nullable=True)  # Optional for per-section mapping
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True)  # Reference Staff table

    # Relationships
    cls = relationship("Classes", backref="class_subject_links")  # Renamed backref to avoid conflict
    section = relationship("Section", backref="subject_mappings")  # Renamed backref to avoid conflict
    subject = relationship("Subject", back_populates="class_subject_mappings")  # Ensure this matches the Subject model
    teacher = relationship("Staff", backref="class_subject_mappings")  # Link to Staff table

    __table_args__ = (
        Index('idx_class_subject_mapping_class_id', 'class_id'),
        Index('idx_class_subject_mapping_section_id', 'section_id'),
        Index('idx_class_subject_mapping_subject_id', 'subject_id'),
        Index('idx_class_subject_mapping_teacher_id', 'teacher_id'),
    )


class SubjectTeacherMappings(AuditModel):  # Renamed from SubjectTeachers
    __tablename__ = "subject_teacher_mappings"

    teacher_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"))  # Reference Staff table
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True)

    assigned_on = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    teacher = relationship("Staff", back_populates="subject_links")  # Link to Staff table
    subject = relationship("Subject", back_populates="teachers")

    __table_args__ = (
        Index('idx_subject_teacher_teacher_id', 'teacher_id'),
        Index('idx_subject_teacher_subject_id', 'subject_id'),
    )
