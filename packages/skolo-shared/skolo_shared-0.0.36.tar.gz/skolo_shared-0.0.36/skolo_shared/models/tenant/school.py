from sqlalchemy import Column, String, Float

from ..common import AuditModel


class SchoolLocationBoundary(AuditModel):
    """
    Stores detailed school information and geolocation boundary (lat/lng radius).
    """
    __tablename__ = 'school_location_boundary'

    school_name = Column(String(255), nullable=False)
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    phone_number = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    established_year = Column(String(10), nullable=True)
    total_students = Column(Float, nullable=True)
    campus_area_sq_m = Column(Float, nullable=True)
    center_latitude = Column(Float, nullable=False)
    center_longitude = Column(Float, nullable=False)
    radius_in_meters = Column(Float, nullable=False)  # e.g., 100 meters
