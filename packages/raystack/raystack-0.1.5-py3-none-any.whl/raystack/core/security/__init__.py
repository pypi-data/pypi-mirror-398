# Security utilities are optional - projects should install dependencies if needed
try:
    from .jwt import create_access_token
except ImportError:
    create_access_token = None

try:
    from .password import pwd_context, verify_password, get_password_hash
except ImportError:
    pwd_context = None
    verify_password = None
    get_password_hash = None