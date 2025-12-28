# Time Zone Guidelines for skolo-shared Models

This document provides comprehensive guidance on handling time zones in the skolo-shared SQLAlchemy models. All datetime columns in this repository are configured to be **time zone aware** with **UTC as the default time zone**.

## Overview

### Why Time Zone Awareness Matters

- **Data Consistency**: Storing all timestamps in UTC ensures consistency across different time zones
- **Accurate Comparisons**: UTC timestamps allow accurate comparison of events across different geographical locations
- **Avoid Ambiguity**: Time zone aware timestamps eliminate ambiguity caused by daylight saving time (DST) changes
- **International Support**: Schools operating in multiple time zones or with international students benefit from standardized time handling

## Implementation Standards

### SQLAlchemy DateTime Column Definition

All `DateTime` columns in the skolo-shared models **MUST** use `timezone=True`:

```python
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func

# ✅ CORRECT - Time zone aware
created_at = Column(DateTime(timezone=True), server_default=func.now())
start_date = Column(DateTime(timezone=True), nullable=False)
event_date = Column(DateTime(timezone=True), nullable=True)

# ❌ INCORRECT - Not time zone aware (DO NOT USE)
created_at = Column(DateTime, server_default=func.now())
start_date = Column(DateTime, nullable=False)
```

### Base Model Configuration

The `BaseModel` class in `skolo_shared/models/common/base_model.py` already includes time zone aware timestamp columns:

```python
class BaseModel(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(SAEnum(StatusEnum, name="statusenum"), default=StatusEnum.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
```

All models inheriting from `BaseModel` or `AuditModel` automatically get these time zone aware columns.

## Working with Time Zone Aware Columns

### Inserting Data

When inserting datetime values, always use UTC:

```python
from datetime import datetime, timezone

# ✅ CORRECT - Using UTC
event = EventNews(
    title="Parent Meeting",
    event_date=datetime.now(timezone.utc),
    registration_deadline=datetime(2025, 3, 15, 14, 0, 0, tzinfo=timezone.utc)
)

# ✅ CORRECT - Using func.now() for current timestamp (returns UTC on properly configured DB)
from sqlalchemy.sql import func
event = EventNews(
    title="Parent Meeting",
    event_date=func.now()
)

# ❌ INCORRECT - Naive datetime without timezone
event = EventNews(
    title="Parent Meeting",
    event_date=datetime.now()  # DO NOT USE - timezone naive
)
```

### Querying Data

When querying, ensure your comparison values are also in UTC:

```python
from datetime import datetime, timezone

# ✅ CORRECT - Query with UTC datetime
now_utc = datetime.now(timezone.utc)
upcoming_events = session.query(EventNews).filter(
    EventNews.event_date > now_utc
).all()

# ✅ CORRECT - Using func.now() for database-side comparison
from sqlalchemy.sql import func
upcoming_events = session.query(EventNews).filter(
    EventNews.event_date > func.now()
).all()
```

### Converting to Local Time for Display

When displaying timestamps to users, convert from UTC to the user's local time zone:

```python
from datetime import timezone
from zoneinfo import ZoneInfo  # Python 3.9+

# Fetch the event (stored in UTC)
event = session.query(EventNews).filter_by(id=event_id).first()

# Convert to user's local timezone for display
user_timezone = ZoneInfo("Asia/Kolkata")  # Example: Indian Standard Time
local_event_date = event.event_date.astimezone(user_timezone)

print(f"Event Date (UTC): {event.event_date}")
print(f"Event Date (Local): {local_event_date}")
```

### Accepting User Input

When accepting datetime input from users, convert to UTC before storing:

```python
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def parse_user_datetime(date_string: str, user_timezone_str: str) -> datetime:
    """
    Parse a datetime string from user input and convert to UTC.
    
    Args:
        date_string: The datetime string (e.g., "2025-03-15 14:00:00")
        user_timezone_str: The user's timezone (e.g., "Asia/Kolkata")
    
    Returns:
        A timezone-aware datetime in UTC
    """
    user_tz = ZoneInfo(user_timezone_str)
    # Parse the naive datetime
    naive_dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    # Localize to user's timezone
    local_dt = naive_dt.replace(tzinfo=user_tz)
    # Convert to UTC
    utc_dt = local_dt.astimezone(timezone.utc)
    return utc_dt

# Example usage
user_input = "2025-03-15 14:00:00"
user_timezone = "Asia/Kolkata"
utc_datetime = parse_user_datetime(user_input, user_timezone)

event = EventNews(
    title="Parent Meeting",
    event_date=utc_datetime
)
```

## PostgreSQL Database Configuration

### Recommended Database Settings

Ensure your PostgreSQL database is configured to use UTC:

```sql
-- Set timezone for the database
ALTER DATABASE your_database SET timezone TO 'UTC';

-- Verify current timezone setting
SHOW timezone;
```

### Column Types

When using `DateTime(timezone=True)`, SQLAlchemy creates PostgreSQL columns with type `TIMESTAMP WITH TIME ZONE` (or `TIMESTAMPTZ`):

```sql
-- The resulting column type in PostgreSQL
event_date TIMESTAMP WITH TIME ZONE
```

## Migration Guidelines

### Adding New DateTime Columns

When adding new DateTime columns in migrations, always include timezone awareness:

```python
# In Alembic migration
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column(
        'events_news',
        sa.Column('reminder_date', sa.DateTime(timezone=True), nullable=True)
    )

def downgrade():
    op.drop_column('events_news', 'reminder_date')
```

### Converting Existing Columns

If you need to convert existing naive datetime columns to timezone-aware:

```python
# In Alembic migration
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Convert existing data to UTC (assuming it was stored in UTC but without timezone info)
    op.execute("""
        ALTER TABLE events_news 
        ALTER COLUMN registration_deadline TYPE TIMESTAMP WITH TIME ZONE 
        USING registration_deadline AT TIME ZONE 'UTC'
    """)

def downgrade():
    op.execute("""
        ALTER TABLE events_news 
        ALTER COLUMN registration_deadline TYPE TIMESTAMP WITHOUT TIME ZONE
    """)
```

## Time Zone Aware Models Summary

### All DateTime Columns Are Time Zone Aware

The following models have all their DateTime columns configured with `timezone=True`:

**Common (Base Models):**
- `BaseModel`: `created_at`, `updated_at`, `deleted_at`
- `AuditModel`: Inherits from BaseModel

**Tenant Models:**
- `StudentAttendance`: `attendance_date`, `time_in`, `time_out`
- `EventNews`: `event_date`, `registration_deadline`, `publish_date`, `expiry_date`
- `EventNewsNotification`: `sent_at`
- `EventNewsReadReceipt`: `read_at`
- `EventRegistration`: `registration_date`
- `ExamInstance`: `start_date`, `end_date`, `marksheet_scheduled_generation_date`, `marksheet_actual_publish_date`
- `ExamSubjectMap`: `schedule_date`
- `SchoolExpenditure`: `expenditure_date`
- `StudentFixedFeePaymentScheduleMapping`: `payment_due_date`, `paid_date`
- `Staff`: `date_of_joining`, `date_of_termination`
- `StaffCTCStructure`: `effective_from`, `effective_to`
- `StaffPaymentRecord`: `payment_date`
- `StaffAttendance`: `timestamp`
- `Student`: `date_of_birth`, `enrolment_date`
- `StudentFacilityMapping`: `start_date`, `end_date`
- `AcademicYears`: `start_date`, `end_date`
- `SubjectTeacherMappings`: `assigned_on`
- `DriverTripSession`: `start_time`, `end_time`
- `DriverTripLocation`: `timestamp`
- `UserFile`: `uploaded_at`

**Public Models:**
- `TenantDeployment`: `started_at`, `finished_at`
- `TenantSetting`: `updated_at`
- `User`: `last_login`, `locked_until`, `reset_token_expires_at`
- `LoginHistory`: `login_time`, `logout_time`
- `UserSession`: `issued_at`, `expires_at`
- `ActivityLog`: `timestamp`
- `BlockedIP`: `blocked_at`
- `SecurityAlert`: `created_at`
- `UserPasswordHistory`: `changed_at`

## Best Practices Checklist

When working with datetime in skolo-shared:

- [ ] Always use `DateTime(timezone=True)` for new datetime columns
- [ ] Store all timestamps in UTC
- [ ] Convert user input to UTC before storing
- [ ] Convert UTC to local time only for display purposes
- [ ] Use `datetime.now(timezone.utc)` instead of `datetime.now()`
- [ ] Use `func.now()` for database-side current timestamp
- [ ] Configure your PostgreSQL database timezone to UTC
- [ ] Test datetime handling across different time zones

## Common Pitfalls to Avoid

1. **Using naive datetime objects**: Always ensure datetime objects have timezone information
2. **Storing local time**: Convert all datetime values to UTC before storing
3. **Comparing naive and aware datetimes**: This will raise a `TypeError` in Python
4. **Assuming server timezone**: Always explicitly specify UTC when creating datetime objects
5. **Forgetting to convert for display**: Users expect to see times in their local timezone

## Additional Resources

- [Python datetime documentation](https://docs.python.org/3/library/datetime.html)
- [SQLAlchemy DateTime documentation](https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.DateTime)
- [PostgreSQL Date/Time Types](https://www.postgresql.org/docs/current/datatype-datetime.html)
- [PEP 495 - Local Time Disambiguation](https://www.python.org/dev/peps/pep-0495/)
