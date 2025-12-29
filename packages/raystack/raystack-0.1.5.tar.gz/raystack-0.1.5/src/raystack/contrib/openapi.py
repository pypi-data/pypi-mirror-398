"""
OpenAPI/Swagger UI integration for Raystack.
"""
import json
import re
import inspect
from typing import Any, Dict, List, Optional, get_origin, get_args
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route
from starlette.requests import Request


SWAGGER_UI_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui.css" />
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin:0;
            background: #fafafa;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "/openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            });
        };
    </script>
</body>
</html>
"""


def extract_route_info(route) -> Dict[str, Any]:
    """Extract information from a route."""
    info = {
        "path": None,
        "methods": [],
        "summary": "",
        "description": "",
        "endpoint": None
    }
    
    # Handle Route objects
    if hasattr(route, 'path'):
        info["path"] = route.path
        if hasattr(route, 'methods'):
            info["methods"] = list(route.methods)
        if hasattr(route, 'endpoint'):
            info["endpoint"] = route.endpoint
            # Try to get docstring
            if hasattr(route.endpoint, '__doc__') and route.endpoint.__doc__:
                info["description"] = route.endpoint.__doc__.strip()
            if hasattr(route.endpoint, '__name__'):
                info["summary"] = route.endpoint.__name__.replace('_', ' ').title()
    
    # Handle Mount objects (nested routers)
    elif hasattr(route, 'path') and hasattr(route, 'app'):
        info["path"] = route.path
        # For mounted apps, we need to recursively extract routes
        if hasattr(route.app, 'routes'):
            nested_routes = []
            for nested_route in route.app.routes:
                nested_info = extract_route_info(nested_route)
                if nested_info["path"]:
                    # Combine paths
                    base_path = route.path.rstrip('/')
                    nested_path = nested_info["path"]
                    if nested_path.startswith('/'):
                        nested_path = nested_path[1:]
                    nested_info["path"] = f"{base_path}/{nested_path}" if nested_path else base_path
                    nested_routes.append(nested_info)
            return nested_routes
    
    return info


def generate_openapi_schema(
    title: str = "Raystack API",
    version: str = "0.0.0",
    description: str = "API documentation for Raystack application",
    routes: Optional[List] = None
) -> Dict[str, Any]:
    """
    Generate OpenAPI 3.0 schema from routes.
    """

    def _schema_from_annotation(annotation: Any) -> Dict[str, str]:
        """Map Python type annotations to OpenAPI schema snippets."""
        mapping = {
            int: {"type": "integer"},
            float: {"type": "number"},
            bool: {"type": "boolean"},
            str: {"type": "string"},
        }
        return mapping.get(annotation, {"type": "string"})

    schema = {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": version,
            "description": description,
        },
        "paths": {},
        "components": {
            "schemas": {},
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        }
    }
    
    if routes:
        all_routes = []
        
        def collect_routes(route_list, base_path="", tags=None):
            """Recursively collect all routes."""
            tags = tags or []
            for route in route_list:
                # Handle Route objects
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    path = route.path
                    if base_path:
                        path = f"{base_path.rstrip('/')}{path}"
                    all_routes.append({
                        "path": path,
                        "methods": list(route.methods) if hasattr(route, 'methods') else [],
                        "endpoint": getattr(route, 'endpoint', None),
                        "tags": tags,
                    })
                # Handle Mount objects (nested routers)
                elif hasattr(route, 'path') and hasattr(route, 'app'):
                    mount_path = route.path
                    if base_path:
                        mount_path = f"{base_path.rstrip('/')}{mount_path}"
                    nested_tags = tags + getattr(route.app, "tags", [])
                    if hasattr(route.app, 'routes'):
                        collect_routes(route.app.routes, mount_path, nested_tags)
        
        collect_routes(routes)
        
        # Group routes by path
        for route_info in all_routes:
            path = route_info["path"]
            if not path:
                continue
                
            if path not in schema["paths"]:
                schema["paths"][path] = {}
            
            for method in route_info["methods"]:
                method_lower = method.lower()
                if method_lower in ["get", "post", "put", "delete", "patch"]:
                    endpoint = route_info.get("endpoint")
                    summary = ""
                    description = ""
                    request_body = None
                    parameters: List[Dict[str, Any]] = []
                    path_params = {
                        m.group(1) for m in re.finditer(r"{([^}]+)}", path or "")
                    }
                    
                    if endpoint:
                        if hasattr(endpoint, '__doc__') and endpoint.__doc__:
                            description = endpoint.__doc__.strip()
                        if hasattr(endpoint, '__name__'):
                            summary = endpoint.__name__.replace('_', ' ').title()

                        # Infer request body schema from endpoint annotations
                        try:
                            from pydantic import BaseModel
                            sig = inspect.signature(endpoint)
                            for param in sig.parameters.values():
                                annotation = param.annotation
                                # Skip the request object
                                if getattr(annotation, '__name__', '') == 'Request' or param.name == 'request':
                                    continue
                                origin = get_origin(annotation)
                                args = get_args(annotation)
                                model_cls = None
                                if origin is None and isinstance(annotation, type) and issubclass(annotation, BaseModel):
                                    model_cls = annotation
                                elif origin is list and args and isinstance(args[0], type) and issubclass(args[0], BaseModel):
                                    model_cls = args[0]
                                elif origin is not None and args:
                                    # Handle Optional/Union
                                    for arg in args:
                                        if isinstance(arg, type) and issubclass(arg, BaseModel):
                                            model_cls = arg
                                            break
                                if model_cls:
                                    model_name = model_cls.__name__
                                    schema["components"]["schemas"][model_name] = model_cls.schema()
                                    request_body = {
                                        "required": True,
                                        "content": {
                                            "application/x-www-form-urlencoded": {
                                                "schema": {"$ref": f"#/components/schemas/{model_name}"}
                                            },
                                            "multipart/form-data": {
                                                "schema": {"$ref": f"#/components/schemas/{model_name}"}
                                            }
                                        }
                                    }
                                    break
                                else:
                                    # Treat simple annotated params as path/query parameters
                                    param_in = "path" if param.name in path_params else "query"
                                    parameters.append(
                                        {
                                            "name": param.name,
                                            "in": param_in,
                                            "required": True
                                            if param_in == "path"
                                            or param.default is inspect._empty
                                            else False,
                                            "schema": _schema_from_annotation(annotation),
                                        }
                                    )
                        except Exception:
                            pass

                    # Ensure all path parameters appear in schema even if not in the
                    # endpoint signature (since Starlette passes them via request).
                    for path_param in path_params:
                        if not any(p.get("name") == path_param for p in parameters):
                            parameters.append(
                                {
                                    "name": path_param,
                                    "in": "path",
                                    "required": True,
                                    "schema": {"type": "string"},
                                }
                            )
                    
                    schema["paths"][path][method_lower] = {
                        "summary": summary,
                        "description": description,
                        "tags": route_info.get("tags") or [],
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object"}
                                    }
                                }
                            }
                        },
                        **({"parameters": parameters} if parameters else {}),
                        **({"requestBody": request_body} if request_body else {})
                    }

    return schema


async def openapi_json(request: Request):
    """Serve OpenAPI JSON schema."""
    app = request.app
    schema = generate_openapi_schema(
        title=getattr(app.settings, 'API_TITLE', 'Raystack API'),
        version=getattr(app.settings, 'API_VERSION', '0.0.0'),
        description=getattr(app.settings, 'API_DESCRIPTION', 'API documentation for Raystack application'),
        routes=app.router.routes
    )
    return JSONResponse(schema)


async def swagger_ui(request: Request):
    """Serve Swagger UI HTML."""
    return HTMLResponse(SWAGGER_UI_HTML)


def setup_openapi(app, docs_url: str = "/docs", openapi_url: str = "/openapi.json"):
    """
    Setup OpenAPI/Swagger UI endpoints.
    
    Args:
        app: Starlette application instance
        docs_url: URL path for Swagger UI (default: /docs)
        openapi_url: URL path for OpenAPI JSON schema (default: /openapi.json)
    """
    # Add OpenAPI JSON endpoint - use app.add_route for Starlette
    app.add_route(openapi_url, openapi_json, methods=["GET"])
    
    # Add Swagger UI endpoint
    app.add_route(docs_url, swagger_ui, methods=["GET"])
