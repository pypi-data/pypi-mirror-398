from collections.abc import Generator
from typing import Union

from raystack.compat import Depends, HTTPException, status, Request, OAuth2PasswordBearer
from pydantic import ValidationError
from sqlmodel import Session
from starlette.authentication import SimpleUser # Import SimpleUser from Starlette

# JWT is optional - projects should install pyjwt if needed
try:
    import jwt
    from jwt.exceptions import InvalidTokenError
except ImportError:
    jwt = None
    InvalidTokenError = Exception

# Lazy import to avoid errors when loading
# from raystack.core.database.base import get_async_db, get_sync_engine
try:
    from raystack.core.security.jwt import create_access_token, TokenPayload # Import TokenPayload
except ImportError:
    create_access_token = None
    TokenPayload = None

# Lazy imports to avoid circular dependencies
# UserModel will be imported dynamically from installed apps when needed
UserModel = None

def _get_user_model():
    """Lazy import UserModel from installed apps."""
    global UserModel
    if UserModel is not None:
        return UserModel
    
    try:
        from raystack.conf import get_settings
        settings = get_settings()
        
        # Try to import from installed apps
        for app_path in getattr(settings, 'INSTALLED_APPS', []):
            if 'auth' in app_path.lower() and 'user' in app_path.lower():
                try:
                    # Try to import UserModel from the module
                    parts = app_path.split('.')
                    if len(parts) >= 2:
                        # Try models submodule
                        models_path = '.'.join(parts[:-1]) + '.models'
                        try:
                            module = __import__(models_path, fromlist=['UserModel'])
                            if hasattr(module, 'UserModel'):
                                UserModel = module.UserModel
                                return UserModel
                        except ImportError:
                            pass
                    
                    # Try direct import
                    module = __import__(app_path, fromlist=['UserModel'])
                    if hasattr(module, 'UserModel'):
                        UserModel = module.UserModel
                        return UserModel
                except (ImportError, AttributeError):
                    continue
            
    except Exception:
        pass
    
    # If not found, raise error - UserModel must be provided by installed apps
    raise ImportError(
        "UserModel not found. Make sure you have an auth app with UserModel "
        "in your INSTALLED_APPS (e.g., apps.admin.auth.users)."
    )

def get_api_v1_str():
    try:
        from raystack.conf import get_settings
        return getattr(get_settings(), 'API_V1_STR', '/api/v1')
    except ImportError:
        return '/api/v1'

def get_secret_key():
    try:
        from raystack.conf import get_settings
        return getattr(get_settings(), 'SECRET_KEY', 'default-secret-key')
    except ImportError:
        return 'default-secret-key'

def get_algorithm():
    try:
        from raystack.conf import get_settings
        return getattr(get_settings(), 'ALGORITHM', 'HS256')
    except ImportError:
        return 'HS256'

_reusable_oauth2 = None

def get_reusable_oauth2():
    global _reusable_oauth2
    if _reusable_oauth2 is None:
        _reusable_oauth2 = OAuth2PasswordBearer(
            tokenUrl=f"{get_api_v1_str()}/login/access-token"
        )
    return _reusable_oauth2

def get_db():
    try:
        from raystack.core.database.base import get_sync_engine
        with Session(get_sync_engine()) as session: # Use get_sync_engine() to create synchronous session
            yield session
    except ImportError:
        # Fallback if database is not configured
        raise RuntimeError("Database is not configured")

# For Python 3.6 compatibility, we'll use regular types instead of Annotated
SessionDep = Session
TokenDep = str
# UserDep will be defined after UserModel is loaded
UserDep = None

def get_current_user(request: Request, session: SessionDep, token: TokenDep = Depends(get_reusable_oauth2)):
    # Lazy load UserModel
    UserModel = _get_user_model()
    
    # First, check if user is already authenticated by middleware
    if "user" in request.scope and request.scope["user"] is not None:
        simple_user: SimpleUser = request.scope["user"]
        # Assuming SimpleUser.identity is the user ID
        user_id = int(simple_user.identity)
        user = session.get(UserModel, user_id)
        if user:
            if not user.is_active:
                raise HTTPException(status_code=400, detail="Inactive user")
            return user
        
    # If not authenticated by middleware, try to authenticate via JWT token from header
    if jwt is None or TokenPayload is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT support not available. Install pyjwt: pip install pyjwt",
        )
    
    try:
        payload = jwt.decode(
            token, get_secret_key(), algorithms=[get_algorithm()]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(UserModel, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

def get_current_active_superuser(current_user):
    UserModel = _get_user_model()
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user