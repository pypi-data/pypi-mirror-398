from sqlalchemy import Column, String, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..common import AuditModel


class Driver(AuditModel):
    """
    Driver model.
    """
    __tablename__ = 'drivers'
    staff_id = Column(UUID(as_uuid=True), ForeignKey('staff.id'), nullable=False)
    driver_name = Column(String(255), nullable=False)
    license_number = Column(String(255), nullable=False)
    contact_number = Column(String(20), nullable=False)
    address = Column(String(255), nullable=False)

    staff = relationship("Staff", backref="driver_profile")
    # Use string-based relationship to avoid circular import
    trip_sessions = relationship('DriverTripSession', back_populates='driver', lazy='dynamic')


class TransportRoute(AuditModel):
    """
    Transport route model.
    """
    __tablename__ = 'transport_routes'
    route_name = Column(String(255), nullable=False)
    distance = Column(Numeric(10, 2), nullable=False)
    description = Column(String(255))
    driver_id = Column(UUID(as_uuid=True), ForeignKey('drivers.id'), nullable=False)
    driver = relationship("Driver")
    student_transport_assignments = relationship("StudentTransportAssignment", back_populates="route")
    transport_route_fee_mappings = relationship("TransportRouteFeeMapping", back_populates="transport_route")

    # Added relationship to DriverTripSession
    trip_sessions = relationship("DriverTripSession", back_populates="route")


class TransportRouteFeeMapping(AuditModel):
    """
    Maps a specific transport route to a specific fee for an academic year.
    Ensures a unique fee applies per route per academic year.
    """
    __tablename__ = 'transport_route_fee_mappings'

    transport_route_id = Column(UUID(as_uuid=True), ForeignKey('transport_routes.id'), nullable=False)
    fee_id = Column(UUID(as_uuid=True), ForeignKey('fees.id'), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic_years.id'), nullable=False)

    # Define unique constraint to ensure uniqueness per route, fee, and academic year
    __table_args__ = (
        UniqueConstraint('transport_route_id', 'fee_id', 'academic_year_id', name='_transport_route_fee_uc'),
    )

    # Relationships
    transport_route = relationship("TransportRoute", back_populates="transport_route_fee_mappings")
    fee = relationship("Fee",
                       back_populates="transport_route_fee_mappings")
    academic_year = relationship("AcademicYears")


class StudentTransportAssignment(AuditModel):
    """
    Student transport assignment model.
    """
    __tablename__ = 'student_transport_assignments'
    student_facility_mapping_id = Column(UUID(as_uuid=True), ForeignKey('student_facility_mapping.id'), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey('transport_routes.id'), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey('drivers.id'), nullable=False)
    # Relationship to StudentFacilityMapping
    student_facility_mapping = relationship("StudentFacilityMapping", back_populates="transport_assignments")

    # Indirect access to Student via StudentFacilityMapping
    @property
    def student(self):
        return self.student_facility_mapping.student if self.student_facility_mapping else None

    # Relationship to TransportRoute
    route = relationship("TransportRoute", back_populates="student_transport_assignments")
    driver = relationship("Driver")
