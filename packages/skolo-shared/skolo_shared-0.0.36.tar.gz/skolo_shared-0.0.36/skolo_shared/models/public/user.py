# user.py

from uuid import uuid4

from ..common import BaseModel, UserType, LoginStatus, DeviceTypeEnum, LoginMethod, StatusBaseModel

from sqlalchemy import Column, DateTime, String, ForeignKey, Boolean, func, Float, Text, JSON
from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SAEnum
from sqlalchemy import UniqueConstraint


class Tenant(BaseModel):
    __tablename__ = 'tenants'
    __table_args__ = {'schema': 'public'}
    name = Column(String(255), unique=True, nullable=False)
    email_id = Column(String(255), nullable=False, unique=True)
    address = Column(String(255), nullable=True)
    schema_name = Column(String(255), unique=True, nullable=False)


class TenantDeployment(BaseModel):
    __tablename__ = 'tenant_deployments'
    __table_args__ = {'schema': 'public'}
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('public.tenants.id'),
                       nullable=True)  # optionally ForeignKey('public.tenants.id')
    schema_name = Column(String(255), nullable=False, index=True)
    deployment_type = Column(String(50), nullable=False, default='MIGRATION')
    migration_revision = Column(String(128), nullable=True)
    status = Column(String(20), nullable=False, default='PENDING', index=True)
    attempts = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    run_by = Column(String(255), nullable=True)
    deployment_metadata = Column(JSON, nullable=True)


class TenantSetting(BaseModel):
    __tablename__ = 'tenant_settings'
    __table_args__ = {'schema': 'public'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('public.tenants.id'), nullable=False, index=True)
    key = Column(String(100), nullable=False)  # e.g., "fees.auto_calculate"
    value = Column(JSONB, nullable=True)  # JSON value for flexibility
    is_enabled = Column(Boolean, default=True, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant")


class UserTypeValue(StatusBaseModel):
    __tablename__ = 'user_type_values'
    __table_args__ = {'schema': 'public'}
    value = Column(String(50), primary_key=True, unique=True, nullable=False)


class User(BaseModel):
    """
    User model for authentication and authorization.
    """
    __tablename__ = 'users'
    __table_args__ = (
        UniqueConstraint("tenant_id", "email"),
        {'schema': 'public'}
    )
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('public.tenants.id'), nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    # Add contact number and address.
    phone_number = Column(String(20))
    address = Column(String(255))
    # Profile image
    profile_image_url = Column(String(255))
    # Add roles for authorization
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    reset_token_hash = Column(String(128), nullable=True)
    reset_token_expires_at = Column(DateTime(timezone=True), nullable=True)

    preferred_language = Column(String(10), default='en')
    timezone = Column(String(50), default='Asia/Kolkata')
    extra_metadata = Column(JSONB, nullable=True)

    roles = relationship("Role", secondary="public.user_roles", back_populates="users")
    tenant = relationship("Tenant")
    user_type = Column(String(50), ForeignKey('public.user_type_values.value'), nullable=False)


# -- Table: login_history
# -- Purpose: Audits every login/logout attempt, storing timestamps and IPs.
# -- Populated When:
# --   - User attempts login (success or failure).
# -- Best Practice:
# --   - Store IP address, user-agent string, and location (if available).
# --   - Useful for detecting suspicious activity or brute force attempts.
# --   - Keep this table pruned periodically for performance.
class LoginHistory(BaseModel):
    __tablename__ = "login_history"
    __table_args__ = {'schema': 'public'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('public.users.id'), nullable=False)
    login_time = Column(DateTime(timezone=True), default=func.now())
    logout_time = Column(DateTime(timezone=True), nullable=True)

    status = Column(
        SAEnum(
            LoginStatus,
            name="login_status_enum",
            native_enum=True,
            create_type=False
        ),
        nullable=False
    )
    failure_reason = Column(String(255), nullable=True)

    ip_address = Column(String(50))
    user_agent = Column(String(255))
    location = Column(String(255))  # e.g., "Kolkata, India"
    device_type = Column(
        SAEnum(
            DeviceTypeEnum,
            name="device_type_enum",
            native_enum=True,
            create_type=False
        ),
        default=DeviceTypeEnum.UNKNOWN
    )
    browser_name = Column(String(50))
    os_name = Column(String(50))
    login_method = Column(
        SAEnum(
            LoginMethod,
            name="login_method_enum",
            native_enum=True,
            create_type=False
        ),
        nullable=False
    )
    session_id = Column(String(100), nullable=True)  # App session or browser session ID
    token_id = Column(String(100), nullable=True)  # JWT/refresh token ID
    is_mobile_app = Column(Boolean, default=False)  # Flag for native skolo_shared login

    user = relationship("User", backref="login_history")


# -- Table: user_sessions
# -- Purpose: Tracks active user sessions and tokens (JWT/session IDs).
# -- Populated When:
# --   - User successfully logs in and receives a session token.
# -- Best Practice:
# --   - Store expiration time, refresh token (if applicable).
# --   - Can be used for "force logout" or session blacklisting.
# --   - Optional but useful for advanced session control.
class UserSession(BaseModel):
    __tablename__ = "user_sessions"
    __table_args__ = {'schema': 'public'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('public.users.id'), nullable=False)
    session_token_hash = Column(String(255), nullable=False, unique=True)
    issued_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    device_info = Column(String(255))
    ip_address = Column(String(50))


# -- Table: activity_logs
# -- Purpose: Stores logs of user actions within the application (create, update, delete, etc.)
# -- Populated When:
# --   - A user performs a critical action (e.g., adding, updating, or deleting data).
# --   - Triggered via service layer or manual logging in the application logic.
# -- Best Practice:
# --   - Store the `user_id`, `tenant_id`, action type (create, update, delete), entity type (student, fee, etc.), and timestamp.
# --   - Useful for security auditing and tracking user activity.
# --   - Can be filtered by `user_id`, `entity_type`, and `action_type` for detailed auditing.
# --   - Periodically archive or prune to avoid excessive table growth.
class ActivityLog(BaseModel):
    __tablename__ = "activity_logs"
    __table_args__ = {'schema': 'public'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('public.users.id'))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('public.tenants.id'))

    action_type = Column(String(100))  # e.g., "CREATE", "UPDATE", "DELETE"
    entity_type = Column(String(100))  # e.g., "Student", "Parent", "FeeRecord"
    entity_id = Column(UUID(as_uuid=True))
    api_endpoint = Column(String(255))  # The API endpoint accessed
    request_method = Column(String(10))  # e.g., "GET", "POST", "PUT", "DELETE"
    request_payload = Column(JSONB)  # JSON payload of the request
    response_status = Column(Integer)  # HTTP status code of the response
    response_payload = Column(JSONB)  # JSON payload of the response
    user_agent = Column(String(255))  # User agent string from the request
    description = Column(String(255))
    timestamp = Column(DateTime(timezone=True), default=func.now())
    ip_address = Column(String(50))


# -- Table: blocked_ips
# -- Purpose: Stores IP addresses that are blocked due to suspicious activity (e.g., brute-force login attempts).
# -- Populated When:
# --   - System detects a certain threshold of failed login attempts (e.g., 5 failed logins).
# --   - Manually added by admin in response to detected abuse.
# -- Best Practice:
# --   - Track blocked IPs along with the reason for blocking and when the block was applied.
# --   - Can be used to prevent abuse from known malicious IP addresses.
# --   - Periodically review blocked IPs and automatically unblock after a certain period or admin approval.
# --   - Useful in combination with rate-limiting and security alerts for login attempts.
class BlockedIP(StatusBaseModel):
    __tablename__ = "blocked_ips"
    __table_args__ = {'schema': 'public'}
    ip_address = Column(String(50), primary_key=True)
    reason = Column(String(255))
    blocked_at = Column(DateTime(timezone=True), default=func.now())


# -- Table: user_2fa_settings
# -- Purpose: Stores the 2FA configuration for each user (whether 2FA is enabled and method used).
# -- Populated When:
# --   - A user enables or disables Two-Factor Authentication (2FA).
# --   - When a user selects the preferred 2FA method (e.g., OTP, TOTP, SMS, Google Authenticator).
# -- Best Practice:
# --   - Store whether 2FA is enabled and the method used (e.g., "EMAIL", "SMS", "TOTP").
# --   - Securely store the `secret_key` for TOTP-based methods (for apps like Google Authenticator).
# --   - Trigger 2FA prompts during login or sensitive actions for users who have 2FA enabled.
# --   - Periodically check if the user is properly using their 2FA method.
class User2FASettings(StatusBaseModel):
    __tablename__ = "user_2fa_settings"
    __table_args__ = {'schema': 'public'}
    user_id = Column(UUID(as_uuid=True), ForeignKey('public.users.id'), primary_key=True)
    is_2fa_enabled = Column(Boolean, default=False)
    method = Column(
        SAEnum(
            "EMAIL", "SMS", "TOTP",
            name="twofa_method_enum",
            native_enum=True,
            create_type=False
        )
    )
    secret_key = Column(String(255), nullable=True)  # For TOTP-based methods


# -- Table: security_alerts
# -- Purpose: Tracks security-related events that may require investigation or user notification.
# -- Populated When:
# --   - A user logs in from a new location/device.
# --   - Multiple failed login attempts to happen in a short window.
# --   - Sensitive action is performed outside allowed policy (e.g., off-hours).
# -- Fields Should Include:
# --   - user_id
# --   - alert_type (FAILED_LOGIN, SUSPICIOUS_ACTIVITY, NEW_DEVICE, etc.)
# --   - details
# --   - created_at
# --   - resolved (bool)
# -- Best Practice:
# --   - Notify admins or users (email/push) for high-severity alerts.
# --   - Auto-resolve some alerts (e.g., "already handled") or allow admin resolution.
# --   - Store metadata like device, IP, tenant_id for context.
class SecurityAlert(BaseModel):
    __tablename__ = "security_alerts"
    __table_args__ = {'schema': 'public'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('public.users.id'))
    alert_type = Column(String(100))  # e.g., "FAILED_LOGIN", "NEW_DEVICE"
    details = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=func.now())
    resolved = Column(Boolean, default=False)


# -- Table: user_password_history
# -- Purpose: Stores past passwords to enforce password history policies (e.g., "Cannot reuse last 5 passwords").
# -- Populated When:
# --   - A user updates their password, storing the hash of the old password in this table.
# --   - Helps prevent the reuse of old passwords to ensure security.
# -- Best Practice:
# --   - Store the hashed value of the previous password(s) to prevent password reuse.
# --   - Keep only a set number of historical passwords (e.g., the last 5 passwords) to reduce table size.
# --   - Enforce policies that prevent users from setting a password that has been used in the recent past.
# --   - Ensure that password history is securely stored and that the data is not accessible in plaintext.
class UserPasswordHistory(BaseModel):
    __tablename__ = "user_password_history"
    __table_args__ = {'schema': 'public'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('public.users.id'))
    password_hash = Column(String(255))
    changed_at = Column(DateTime(timezone=True), default=func.now())
