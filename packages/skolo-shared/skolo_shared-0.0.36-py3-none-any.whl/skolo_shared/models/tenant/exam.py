from sqlalchemy import Column, String, ForeignKey, UUID, DateTime, Integer, Text, Float, Boolean, Index
from sqlalchemy import event
from sqlalchemy.orm import relationship, object_session

from ..common import AuditModel


# High-Level Exam & Marksheet Flow

# Step 1: Setup Exam Template
# Admin or Academic Head creates an ExamTemplate (e.g., Mid Term, Final Term)
# which defines exam-level metadata (grading policy, type, weightage).

# Step 2: Schedule Exam (ExamInstance)
# The template is then used to create an ExamInstance for a specific academic year,
# class, section, and term (e.g., "Final Term 2025 for Class 5-A").

# Step 3: Map Subjects to Exam (ExamSubjectMap)
# For each ExamInstance, subjects are mapped with details like:
#   • Subject
#   • Subject teacher (optional)
#   • Max marks
#   • Passing marks
#   • Exam date/time (optional)
#   • Order of appearance (for result sheet)

# Step 4: Enter Student Marks (StudentMarks)
# Each teacher logs in and enters marks for their subjects per student.
#   • Validation checks ensure max/passing constraints
#   • Data is versioned via AuditTrail in case of later changes

# Step 5: Marksheet Generation
# Once all marks are filled:
#   • A Marksheet (dynamic view or persisted document) is generated
#   • Pulls subject marks, computes totals, applies GradingPolicy
#   • GPA or percentage is calculated (as per configuration)
#   • Optional remarks and class position can be added

# Step 6: Result Publishing
# Marksheet is approved by coordinator/admin, then published to:
#   • Student portal
#   • Parent dashboard
#   • Exported as PDF/print if needed

# Step 7: Change Tracking (AuditTrail)
# Any changes made after publishing are stored in AuditTrail with:
#   • User who made the change
#   • Previous vs new value
#   • Reason/comment
#   • Timestamp for traceability

# 📌 Example Scenario:
# Let’s say “Class 7-B” is having its Midterm Exam:
#   • Admin creates an ExamTemplate named “Mid Term”.
#   • ExamInstance is scheduled for Class 7-B for October 2025.
#   • Subjects like Math, Science, History are mapped with respective teachers
#     and max/passing marks.
#   • Teachers enter student scores in the portal.
#   • Backend computes the result using the grading policy.
#   • A final mark sheet is auto-generated per student and can be viewed/downloaded.
#   • Later, if a mark is updated, an AuditTrail is created automatically.

class ExamTemplate(AuditModel):
    __tablename__ = "exam_templates"

    name = Column(String, nullable=False)  # e.g., "Term 1", "Final"
    duration_minutes = Column(Integer, nullable=True)
    description = Column(Text)
    grading_policy_id = Column(UUID(as_uuid=True), ForeignKey("grading_policies.id"), nullable=True)
    total_marks = Column(Float, nullable=True)  # Add total marks for the exam
    remarks = Column(Text, nullable=True)  # Add remarks for the exam
    grading_policy = relationship("GradingPolicy", backref="exam_templates")

    @staticmethod
    def validate_total_marks(total_marks):
        if total_marks is not None and total_marks < 0:
            raise ValueError("Total marks cannot be negative.")

    @staticmethod
    def validate_name(name):
        if not name.strip():
            raise ValueError("Exam template name cannot be empty.")

# Add event listener for validation
@event.listens_for(ExamTemplate, "before_insert")
@event.listens_for(ExamTemplate, "before_update")
def validate_exam_template(mapper, connection, target):
    target.validate_total_marks(target.total_marks)
    target.validate_name(target.name)


class ExamInstance(AuditModel):
    __tablename__ = "exam_instances"

    template_id = Column(UUID(as_uuid=True), ForeignKey("exam_templates.id"), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"))
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    marksheet_scheduled_generation_date = Column(DateTime(timezone=True), nullable=True)  # Scheduled date for marksheet generation
    marksheet_actual_publish_date = Column(DateTime(timezone=True), nullable=True)  # Actual date when marksheet was published
    total_marks = Column(Float, nullable=True)  # Add total marks for the instance
    remarks = Column(Text, nullable=True)  # Add overall remarks for the instance

    template = relationship("ExamTemplate", backref="exam_instances")

    @staticmethod
    def validate_dates(start_date, end_date):
        if start_date >= end_date:
            raise ValueError("Start date must be before end date.")

# Add event listener for validation
@event.listens_for(ExamInstance, "before_insert")
@event.listens_for(ExamInstance, "before_update")
def validate_exam_instance(mapper, connection, target):
    target.validate_dates(target.start_date, target.end_date)


class ExamSubjectMap(AuditModel):
    __tablename__ = "exam_subject_maps"

    exam_instance_id = Column(UUID(as_uuid=True), ForeignKey("exam_instances.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"),
                        nullable=True)  # Assign a teacher for this subject who will enter marks.
    # This field is nullable, allowing all teachers to enter marks for this subject if no specific teacher is assigned.
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)  # Add foreign key for Subject
    max_marks = Column(Float, nullable=False)
    passing_marks = Column(Float, nullable=False)
    schedule_date = Column(DateTime(timezone=True), nullable=True)  # Add schedule date for the subject when the exam will be conducted
    order_of_appearance = Column(Integer, nullable=True)  # Order in which this subject appears in the marksheet

    # Relationships
    exam_instance = relationship("ExamInstance", backref="exam_subjects")
    subject = relationship("Subject")  # Removed backref to avoid conflict
    teacher = relationship("Staff", backref="exam_subject_mappings")

    # Validation: Ensure max_marks > passing_marks
    @staticmethod
    def validate_marks(max_marks, passing_marks):
        if max_marks <= passing_marks:
            raise ValueError("Max marks must be greater than passing marks.")


class StudentMarks(AuditModel):
    __tablename__ = "student_marks"

    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), nullable=False)
    exam_subject_map_id = Column(UUID(as_uuid=True), ForeignKey("exam_subject_maps.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"),
                        nullable=True)  # Actual Teacher who entered the marks
    marks_obtained = Column(Float, nullable=True)
    marks_obtained_percentage = Column(Float, nullable=True)  # Add percentage field for marksheet generation
    remarks = Column(Text)
    is_absent = Column(Boolean, default=False)
    grade = Column(String(10), nullable=True)  # Add grade field for marksheet generation
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"))

    # Relationships
    exam_subject_map = relationship("ExamSubjectMap")
    student = relationship("Student", foreign_keys=[student_id])  # Specify foreign_keys to resolve ambiguity
    # Relationship to MarksAuditTrail: one StudentMarks may have multiple audit entries
    audit_trail_entries = relationship("MarksAuditTrail", back_populates="mark")

    def calculate_and_update_percentage_and_grade(self, session):
        """
        Calculate marks_obtained_percentage and grade based on marks_obtained,
        max_marks from ExamSubjectMap, and grading policy from ExamTemplate.
        """
        if self.marks_obtained is not None:
            # Fetch related ExamSubjectMap and ExamTemplate
            exam_subject_map = session.query(ExamSubjectMap).filter_by(id=self.exam_subject_map_id).first()
            if not exam_subject_map:
                raise ValueError("ExamSubjectMap not found.")

            max_marks = exam_subject_map.max_marks
            exam_instance = exam_subject_map.exam_instance
            grading_policy = exam_instance.template.grading_policy

            # Calculate percentage
            self.marks_obtained_percentage = (self.marks_obtained / max_marks) * 100

            # Determine grade based on grading policy
            if grading_policy:
                for rule in grading_policy.grade_rules:
                    if rule.min_percentage <= self.marks_obtained_percentage <= rule.max_percentage:
                        self.grade = rule.grade
                        break
            else:
                self.grade = None  # No grading policy defined


@event.listens_for(StudentMarks, "before_insert")
@event.listens_for(StudentMarks, "before_update")
def update_percentage_and_grade(mapper, connection, target):
    session = object_session(target)
    target.calculate_and_update_percentage_and_grade(session)


class GradingPolicy(AuditModel):
    __tablename__ = "grading_policies"

    name = Column(String, nullable=False, unique=True)

    # Add relationship to GradeRule
    grade_rules = relationship("GradeRule", back_populates="grading_policy")  # Define the relationship


class GradeRule(AuditModel):
    __tablename__ = "grade_rules"

    grading_policy_id = Column(ForeignKey("grading_policies.id"), nullable=False)
    min_percentage = Column(Float, nullable=False)
    max_percentage = Column(Float, nullable=False)
    grade = Column(String, nullable=False)

    # Relationships
    grading_policy = relationship("GradingPolicy",
                                  back_populates="grade_rules")  # Ensure this matches the GradingPolicy model

    @staticmethod
    def validate_percentage_range(min_percentage, max_percentage):
        if min_percentage >= max_percentage:
            raise ValueError("Minimum percentage must be less than maximum percentage.")

# Add event listener for validation
@event.listens_for(GradeRule, "before_insert")
@event.listens_for(GradeRule, "before_update")
def validate_grade_rule(mapper, connection, target):
    target.validate_percentage_range(target.min_percentage, target.max_percentage)


class MarksAuditTrail(AuditModel):
    __tablename__ = "marks_audit_trail"

    student_mark_id = Column(UUID(as_uuid=True), ForeignKey("student_marks.id"), nullable=False)
    old_value = Column(Float)
    new_value = Column(Float)
    reason = Column(Text, nullable=True)  # Add reason for the change
    # Relationships
    mark = relationship("StudentMarks", back_populates="audit_trail_entries")

# Indexing for performance
Index("idx_student_marks_student_id", StudentMarks.student_id)
Index("idx_exam_subject_map_exam_instance_id", ExamSubjectMap.exam_instance_id)
Index("idx_exam_subject_map_subject_id", ExamSubjectMap.subject_id)
