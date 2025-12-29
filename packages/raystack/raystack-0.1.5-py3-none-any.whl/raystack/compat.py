"""
Compatibility layer for FastAPI -> Starlette migration.
Provides FastAPI-like API on top of Starlette.
"""
from starlette.routing import Router
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_303_SEE_OTHER, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR
from typing import Any, Callable, Optional
from functools import wraps
import inspect


# Export Starlette classes as FastAPI-compatible names
__all__ = [
    'APIRouter',
    'Request',
    'HTMLResponse',
    'RedirectResponse',
    'JSONResponse',
    'Response',
    'HTTPException',
    'status',
    'Depends',
    'OAuth2PasswordBearer',
]


class APIRouter(Router):
    """
    FastAPI-compatible router based on Starlette Router.
    """
    def __init__(self, prefix: str = "", tags: Optional[list] = None, **kwargs):
        super().__init__(**kwargs)
        self.prefix = prefix
        self.tags = tags or []
        self._routes = []
    
    def include_router(self, router: 'APIRouter', prefix: str = "", tags: Optional[list] = None, include_in_schema: bool = True):
        """
        Include another router into this router.
        """
        full_prefix = self.prefix + prefix
        if tags:
            combined_tags = self.tags + tags
        else:
            combined_tags = self.tags
        
        # Mount the router with the combined prefix
        # In Starlette, mount() adds a Mount route to the router
        if full_prefix:
            # Mount with prefix
            self.mount(full_prefix, router)
        else:
            # Mount without prefix - add all routes directly to this router
            # This is needed because mount("", router) doesn't work as expected
            for route in router.routes:
                self.routes.append(route)
    
    def _filter_starlette_kwargs(self, kwargs: dict) -> dict:
        """Filter kwargs to only include those supported by Starlette Router."""
        # Starlette Router.add_route() supports: path, endpoint, methods, name, include_in_schema
        # FastAPI-specific kwargs to ignore: response_model, tags, dependencies, status_code, etc.
        supported = {'name', 'include_in_schema'}
        return {k: v for k, v in kwargs.items() if k in supported}
    
    def add_api_route(self, path: str, endpoint: Callable, methods: Optional[list] = None, **kwargs):
        """
        FastAPI-compatible method to add a route.
        Equivalent to add_route but filters FastAPI-specific kwargs.
        """
        if methods is None:
            methods = ["GET"]
        filtered_kwargs = self._filter_starlette_kwargs(kwargs)
        return self.add_route(path, endpoint, methods=methods, **filtered_kwargs)
    
    def get(self, path: str, **kwargs):
        """Decorator for GET routes."""
        def decorator(func: Callable):
            filtered_kwargs = self._filter_starlette_kwargs(kwargs)
            return self.add_route(path, func, methods=["GET"], **filtered_kwargs)
        return decorator
    
    def post(self, path: str, **kwargs):
        """Decorator for POST routes."""
        def decorator(func: Callable):
            filtered_kwargs = self._filter_starlette_kwargs(kwargs)
            return self.add_route(path, func, methods=["POST"], **filtered_kwargs)
        return decorator
    
    def put(self, path: str, **kwargs):
        """Decorator for PUT routes."""
        def decorator(func: Callable):
            filtered_kwargs = self._filter_starlette_kwargs(kwargs)
            return self.add_route(path, func, methods=["PUT"], **filtered_kwargs)
        return decorator
    
    def delete(self, path: str, **kwargs):
        """Decorator for DELETE routes."""
        def decorator(func: Callable):
            filtered_kwargs = self._filter_starlette_kwargs(kwargs)
            return self.add_route(path, func, methods=["DELETE"], **filtered_kwargs)
        return decorator
    
    def patch(self, path: str, **kwargs):
        """Decorator for PATCH routes."""
        def decorator(func: Callable):
            filtered_kwargs = self._filter_starlette_kwargs(kwargs)
            return self.add_route(path, func, methods=["PATCH"], **filtered_kwargs)
        return decorator


class HTTPException(Exception):
    """HTTP exception for error responses."""
    def __init__(self, status_code: int, detail: Any = None, headers: Optional[dict] = None):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers


# Status codes module
class status:
    HTTP_200_OK = HTTP_200_OK
    HTTP_201_CREATED = HTTP_201_CREATED
    HTTP_303_SEE_OTHER = HTTP_303_SEE_OTHER
    HTTP_400_BAD_REQUEST = HTTP_400_BAD_REQUEST
    HTTP_401_UNAUTHORIZED = HTTP_401_UNAUTHORIZED
    HTTP_403_FORBIDDEN = HTTP_403_FORBIDDEN
    HTTP_404_NOT_FOUND = HTTP_404_NOT_FOUND
    HTTP_422_UNPROCESSABLE_ENTITY = HTTP_422_UNPROCESSABLE_ENTITY
    HTTP_500_INTERNAL_SERVER_ERROR = HTTP_500_INTERNAL_SERVER_ERROR


# Dependency injection system
class Depends:
    """
    Dependency injection system compatible with FastAPI's Depends.
    """
    def __init__(self, dependency: Callable):
        self.dependency = dependency
    
    async def __call__(self, request: Request):
        """Resolve the dependency."""
        if inspect.iscoroutinefunction(self.dependency):
            return await self.dependency(request)
        else:
            return self.dependency(request)


# OAuth2PasswordBearer replacement
class OAuth2PasswordBearer:
    """
    OAuth2 password bearer token extractor.
    """
    def __init__(self, tokenUrl: str, scheme_name: Optional[str] = None):
        self.tokenUrl = tokenUrl
        self.scheme_name = scheme_name or "OAuth2"
    
    async def __call__(self, request: Request) -> str:
        """Extract token from Authorization header."""
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated"
            )
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authentication scheme"
            )
        return token




