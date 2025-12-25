import ast
import importlib
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from lamina.main import LAMINA_REGISTRY
from lamina.openapi import ExtraResponsesDict
from lamina.openapi.generator import SwaggerGenerator
from lamina.openapi.types import (
    OpenAPIContactObject,
    OpenAPIExternalDocumentationObject,
    OpenAPILicenseObject,
    OpenAPIObject,
    OpenAPIServerObject,
    OpenAPITagsObject,
)
from lamina.openapi.view_data import ViewData

_modules_imported: bool = False


def _module_imports_lamina(py_file: Path) -> bool:
    """Check if a Python file imports lamina.

    Args:
        py_file: Path to Python file to check

    Returns:
        True if the file imports lamina, False otherwise
    """
    try:
        content = py_file.read_text(encoding="utf-8")
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("lamina"):
                        return True
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("lamina"):
                    return True
        return False
    except Exception:
        logger.warning(f"Could not parse {py_file} to check for lamina imports")
        return False


def _import_project_modules() -> None:
    """Import all modules from the user's project that import lamina.

    Walks through the current working directory to find Python modules
    that import lamina, then imports them to trigger decorator registration
    in LAMINA_REGISTRY. Only imports modules that haven't been loaded yet.
    """
    global _modules_imported
    if _modules_imported:
        logger.debug("Already imported project modules")
        return

    project_root = Path.cwd()

    # Find all Python files in the project that import lamina
    for py_file in project_root.rglob("*.py"):
        # Skip __pycache__ and other non-module files
        if "__pycache__" in str(py_file) or py_file.name.startswith("."):
            continue

        # Skip files that don't import lamina
        if not _module_imports_lamina(py_file):
            continue

        # Convert file path to module name
        relative_path = py_file.relative_to(project_root)
        module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]

        # Skip __init__ files and files that would create invalid module names
        if relative_path.stem == "__init__":
            continue

        module_name = ".".join(module_parts)

        # Skip if already imported
        if module_name in sys.modules:
            logger.debug(f"{module_name} already imported.")
            continue

        # Try to import the module
        importlib.import_module(module_name)
        logger.debug(f"Imported project module {module_name}")

    _modules_imported = True


def get_openapi_spec(
    *,
    title: str = "Lamina API",
    version: str = "1.0.0",
    summary: str | None = None,
    description: str | None = None,
    servers: Optional[List[OpenAPIServerObject]] = None,
    host: Optional[str] = None,
    base_path: str = "/",
    security_schemes: Optional[Dict[str, Any]] = None,
    security: Optional[List[Dict[str, List[str]]]] = None,
    contact: Optional[OpenAPIContactObject] = None,
    terms_of_service: str | None = None,
    license_info: Optional[OpenAPILicenseObject] = None,
    external_docs: Optional[OpenAPIExternalDocumentationObject] = None,
    tags: Optional[OpenAPITagsObject] = None,
    extra_responses: Optional[Dict[str, ExtraResponsesDict]] = None,
) -> OpenAPIObject:
    """Generate an OpenAPI 3.1 specification from all lamina-decorated handlers."""

    # Import project modules that use lamina to populate LAMINA_REGISTRY
    _import_project_modules()

    view_data = []
    for wrapper in LAMINA_REGISTRY:
        request_content_type = getattr(
            wrapper, "request_content_type", "application/json"
        )
        response_content_type = getattr(
            wrapper, "response_content_type", "application/json"
        )

        payload = {
            "request": getattr(wrapper, "schema_in", None),
            "response": getattr(wrapper, "schema_out", None),
            "params": getattr(wrapper, "params_in", None),
            "methods": getattr(wrapper, "methods", None),
            "tags": getattr(wrapper, "tags", None),
            "extra_responses": getattr(wrapper, "responses", {}) or {},
            "view_docstring": getattr(wrapper, "__doc__", None),
            "import_path": getattr(wrapper, "import_path", None),
            "path": getattr(wrapper, "path", None),
            "file_last_update": getattr(wrapper, "last_updated", None),
            "accept_media_type": request_content_type,
            "produce_media_type": response_content_type,
        }

        if (
            payload["request"] is None
            and payload["response"] is None
            and payload["params"] is None
        ):
            logger.warning(
                f"Skipping handler with no schemas: {payload['import_path']}"
            )
            continue

        view = ViewData(**payload)
        view_data.append(view)

    # Sort List based on path
    view_data.sort(key=lambda v: v.get_path())

    gen = SwaggerGenerator(view_data=view_data, extra_responses=extra_responses or {})

    return gen.generate(
        title=title,
        version=version,
        host=host,
        base_path=base_path,
        servers=servers,
        summary=summary,
        description=description,
        contact=contact,
        license_info=license_info,
        terms_of_service=terms_of_service,
        security_schemes=security_schemes,
        security=security,
        external_docs=external_docs,
        tags=tags,
    )
