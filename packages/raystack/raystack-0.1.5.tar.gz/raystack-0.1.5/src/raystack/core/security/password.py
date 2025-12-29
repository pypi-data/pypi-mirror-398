# Password hashing is optional - projects should install passlib[bcrypt] if needed
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except ImportError:
    pwd_context = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if pwd_context is None:
        raise ImportError(
            "passlib[bcrypt] is required for password verification. "
            "Install it with: pip install passlib[bcrypt]"
        )
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    if pwd_context is None:
        raise ImportError(
            "passlib[bcrypt] is required for password hashing. "
            "Install it with: pip install passlib[bcrypt]"
        )
    return pwd_context.hash(password)