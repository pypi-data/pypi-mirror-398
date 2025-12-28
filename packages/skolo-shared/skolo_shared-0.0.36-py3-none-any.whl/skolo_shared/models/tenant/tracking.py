from sqlalchemy import Column, ForeignKey, DateTime, Float, func, Enum, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..common import AuditModel
from ..common import TripStatusEnum


# OVERVIEW
# 👤 Actors:
# - Driver (mobile skolo_shared): Sends location in real-time.
# - Backend server: Receives, stores, streams live location.
# - Parent (mobile skolo_shared): Views child's transporter with real-time updates.

# Workflow:
# [Driver App] ---> (Send GPS coordinates every 5 seconds)
#          |
#          v
#   [API Gateway / Auth Layer]
#          |
#          v
#   [Backend Service] ---> [Database] ←→ [Trip Records / Location Logs]
#          |
#          v
#   [WebSocket Server / Redis PubSub / MQTT]
#          |
#          v
#   [Parent App] ---> (Subscribe to child's transporter live feed)

# 🚀 FUTURE-READY UPGRADES
# Features:
# - Geo-fencing: Alert when bus reaches home/school zone.
# - Notification system: Push alerts for start/stop.
# - Heatmap dashboard: Admin view of all live buses.
# - Trip summary: Distance, duration, route logs.
# - Replay route: Show past trip animation.
# - ML anomaly detection: Detect route diversion or delays.


class DriverTripSession(AuditModel):
    __tablename__ = 'driver_trip_sessions'

    driver_id = Column(UUID(as_uuid=True), ForeignKey('drivers.id'), nullable=False, index=True)
    route_id = Column(UUID(as_uuid=True), ForeignKey('transport_routes.id'), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(TripStatusEnum), default=TripStatusEnum.ACTIVE)
    remarks = Column(String(255), nullable=True)

    # Relationships
    driver = relationship('Driver', back_populates='trip_sessions')
    route = relationship('TransportRoute', back_populates='trip_sessions')  # Fixed relationship to reference the class
    locations = relationship("DriverTripLocation", back_populates="trip_session", cascade="all, delete-orphan")


class DriverTripLocation(AuditModel):
    __tablename__ = 'driver_trip_locations'

    trip_session_id = Column(UUID(as_uuid=True), ForeignKey('driver_trip_sessions.id'), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=func.now())

    trip_session = relationship("DriverTripSession", back_populates="locations")

    # Add an index for geospatial queries
    __table_args__ = (
        Index('idx_lat_long', 'latitude', 'longitude'),
    )
