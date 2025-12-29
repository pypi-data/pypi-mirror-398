__version__ = "0.1.5"

import os
import logging
# import importlib.util
import importlib
import sqlite3

from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles
from starlette.responses import JSONResponse

from raystack.conf import settings
from raystack import shortcuts


def setup():
    """
    Configure the settings module if not already configured.
    """
    if not settings.configured:
        settings.configure()


logger = logging.getLogger("uvicorn")


class Raystack(Starlette):

    def __init__(self):
        super().__init__()

        self.settings = settings
        self.shortcuts = shortcuts

        # Get absolute path to current directory
        self.raystack_directory = os.path.dirname(os.path.abspath(__file__))
        
        # Include OpenAPI first, before other routers
        self.include_openapi()
        # Include routers
        self.include_routers()
        self.include_templates()
        self.include_static()
        self.include_middleware()
        self.include_exception_handlers()

    def include_routers(self):
        # Check and import installed applications
        logger.info(f"Loading apps and routers:")
        for app_path in self.settings.INSTALLED_APPS:
            # Dynamically import module
            module = importlib.import_module(app_path)
            logger.info(f"✅'{app_path}'")

            # If module contains routers, include them
            if hasattr(module, "router"):
                # In Starlette, when mounting with empty path, add routes directly
                # instead of using mount("", ...) to avoid nested mount issues
                if hasattr(module.router, 'routes'):
                    # Add all routes from the router directly to avoid nested mount problems
                    for route in module.router.routes:
                        self.router.routes.append(route)
                else:
                    # Fallback to mount if router doesn't have routes attribute
                    self.mount("", module.router)
                logger.info(f"✅'{app_path}.router'")
            else:
                logger.warning(f"⚠️ '{app_path}.router'")

    def include_templates(self):
        # Templates are now project-specific, not part of framework
        # Projects should configure TEMPLATES['DIRS'] in their settings
        pass

    def include_static(self):
        # Include static files from STATICFILES_DIRS
        static_url = getattr(self.settings, 'STATIC_URL', '/static')
        if static_url:
            # Normalize URL prefix
            static_url = '/' + static_url.strip('/')
        else:
            static_url = '/static'

        if hasattr(self.settings, 'STATICFILES_DIRS') and self.settings.STATICFILES_DIRS:
            for static_dir in self.settings.STATICFILES_DIRS:
                if os.path.exists(static_dir):
                    self.mount(static_url, StaticFiles(directory=static_dir), name="static")
                    break  # Mount only the first existing directory
        # Fallback to default static directory
        elif hasattr(self.settings, 'STATIC_URL') and self.settings.STATIC_URL:
            dir_name = self.settings.STATIC_URL.strip('/')
            static_dir = os.path.join(self.settings.BASE_DIR, dir_name)
            if os.path.exists(static_dir):
                self.mount(static_url, StaticFiles(directory=static_dir), name="static")

    def include_middleware(self):
        # Include middleware from settings
        if hasattr(self.settings, 'MIDDLEWARE') and self.settings.MIDDLEWARE:
            logger.info(f"Loading middleware:")
            for middleware_path in self.settings.MIDDLEWARE:
                try:
                    # Import middleware class
                    module_path, class_name = middleware_path.rsplit('.', 1)
                    module = importlib.import_module(module_path)
                    middleware_class = getattr(module, class_name)
                    
                    # Add middleware
                    self.add_middleware(middleware_class)
                    logger.info(f"✅'{middleware_path}'")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load middleware '{middleware_path}': {e}")
    
    def include_exception_handlers(self):
        """Attach framework-level exception handlers."""
        async def db_operational_error_handler(request, exc: sqlite3.OperationalError):
            return JSONResponse(
                status_code=500,
                content={
                    "message": "Database error. Run 'raystack makemigrations' and 'raystack migrate' before calling this endpoint.",
                    "detail": str(exc),
                },
            )

        self.add_exception_handler(sqlite3.OperationalError, db_operational_error_handler)
    
    def include_openapi(self):
        """Include OpenAPI/Swagger UI documentation."""
        try:
            from raystack.contrib.openapi import setup_openapi
            docs_url = getattr(self.settings, 'DOCS_URL', '/docs')
            openapi_url = getattr(self.settings, 'OPENAPI_URL', '/openapi.json')
            setup_openapi(self, docs_url=docs_url, openapi_url=openapi_url)
            logger.info(f"✅ OpenAPI documentation available at {docs_url}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to setup OpenAPI: {e}")
