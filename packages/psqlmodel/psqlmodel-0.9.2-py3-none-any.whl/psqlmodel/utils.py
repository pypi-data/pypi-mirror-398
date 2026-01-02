# psqlmodel/utils.py
import uuid as py_uuid
from datetime import datetime, timezone

__all__ = [
    "gen_default_uuid",
    "now",
    "current_date",
    "Interval",
    "gen_salt",
    "crypt",
]

def gen_default_uuid():
    """Generate a new UUID4 as string.
    
    Can be used as Column default:
        id: uuid = Column(primary_key=True, default=gen_default_uuid)
    """
    return str(py_uuid.uuid4())

def now():
    """
    Returns the current timestamp/time (server-side).
    Maps to PostgreSQL's NOW() function.
    
    Use for TIMESTAMP, TIMESTAMPTZ, and TIME columns:
        created_at: timestamptz = Column(default=now)
        start_time: time = Column(default=now)
    
    For DATE columns, use current_date() instead.
    """
    from psqlmodel.orm.column import RawExpression
    return RawExpression("NOW()")


def current_date():
    """
    Returns the current date (server-side).
    Maps to PostgreSQL's CURRENT_DATE.
    
    Use for DATE columns only:
        birth_date: date = Column(default=current_date)
    """
    from psqlmodel.orm.column import RawExpression
    return RawExpression("CURRENT_DATE")


def Interval(value):
    """
    Returns a PostgreSQL INTERVAL expression.
    
    Args:
        value: Interval specification as string (e.g., '7 days', '1 hour', '30 minutes')
    
    Returns:
        RawExpression representing INTERVAL 'value'
    
    Examples:
        Interval('7 days')      → INTERVAL '7 days'
        Interval('1 hour')      → INTERVAL '1 hour'
        Interval('30 minutes')  → INTERVAL '30 minutes'
        Interval('1 year')      → INTERVAL '1 year'
        
    Usage:
        expires_at=Now() + Interval('7 days')
    """
    from psqlmodel.orm.column import RawExpression
    return RawExpression(f"INTERVAL '{value}'")


def gen_salt(algorithm: str = "bf"):
    """
    PostgreSQL gen_salt() function for password hashing.
    
    Args:
        algorithm: Hash algorithm - 'bf' (bcrypt), 'md5', 'xdes', 'des'
    
    Returns:
        RawExpression for gen_salt('algorithm')
    
    Examples:
        gen_salt()       → gen_salt('bf')
        gen_salt('bf')   → gen_salt('bf')
        gen_salt('md5')  → gen_salt('md5')
        
    Usage:
        crypt('password', gen_salt('bf'))
    
    Note: Requires pgcrypto extension (auto-installed on first use).
    """
    from psqlmodel.orm.column import RawExpression
    return RawExpression(f"gen_salt('{algorithm}')", required_extension="pgcrypto")


def crypt(password, salt):
    """
    PostgreSQL crypt() function for password hashing.
    
    Args:
        password: Plain text password (string or column reference)
        salt: Salt from gen_salt() or stored hash for verification
    
    Returns:
        RawExpression for crypt(password, salt)
    
    Examples:
        # Hash a password
        crypt('mypassword', gen_salt('bf'))
        
        # Verify password (compare with stored hash)
        crypt('input_password', User.password_hash)
        
    Usage in INSERT:
        Insert(User).Select(
            "'email@example.com'",
            crypt('password123', gen_salt('bf')),
            ...
        )
        
    Usage in UPDATE:
        Update(User).Set(password_hash=crypt('newpass', gen_salt('bf')))
        
    Usage in WHERE (verification):
        Select(User).Where(User.password_hash == crypt('input', User.password_hash))
    
    Note: Requires pgcrypto extension (auto-installed on first use).
    """
    from psqlmodel.orm.column import RawExpression
    
    # Handle salt (can be gen_salt() result or column)
    if hasattr(salt, "to_sql"):
        salt_sql = salt.to_sql()
    elif isinstance(salt, RawExpression):
        salt_sql = str(salt)
    else:
        salt_sql = str(salt)
    
    # Handle password (can be string literal or column)
    if hasattr(password, "to_sql"):
        pass_sql = password.to_sql()
    else:
        # Escape single quotes in password
        escaped = str(password).replace("'", "''")
        pass_sql = f"'{escaped}'"
    
    return RawExpression(f"crypt({pass_sql}, {salt_sql})", required_extension="pgcrypto")

