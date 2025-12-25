import datetime
import inspect
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type

from caseconverter import camelcase, kebabcase, titlecase
from pydantic import BaseModel, RootModel
from pydantic_core import PydanticUndefined

from lamina import conf
from lamina.openapi.markdown import markdown_to_html
from lamina.openapi.types import ParameterObject


def extract_schema_info(
    model: Type[BaseModel | RootModel],
) -> Tuple[str, Dict[str, Any]]:
    """Return the JSON Schema reference name and full schema for a Pydantic model."""
    schema = model.model_json_schema(ref_template="#/components/schemas/{model}")
    name = schema.get("title") or model.__name__
    return name, schema


@dataclass
class ViewData:
    """Helper structure to hold collected Pydantic models.

    Attributes:
        request: Optional type for request body.
        response: Optional type for response body.
        params: Optional type for query parameters.
    """

    request: Optional[Type[BaseModel | RootModel]]
    response: Optional[Type[BaseModel | RootModel]]
    params: Optional[Type[BaseModel | RootModel]]
    import_path: Optional[str]
    path: Optional[str] = None
    methods: Optional[List[str]] = None
    extra_responses: Dict[int, Any] = None
    view_docstring: Optional[str] = None
    tags: Optional[List[str]] = None
    file_last_update: Optional[datetime] = None
    accept_media_type: str | None = None
    produce_media_type: str | None = None

    def extract_extras(self) -> Dict[str, Any]:
        """Merge json_schema_extra from provided models."""
        extra_info: Dict[str, Any] = {}
        for m in (self.request, self.response, self.params):
            if m is None:
                continue
            schema = m.model_json_schema()
            # json_schema_extra lands as top-level unknown keys in Pydantic v2
            for key, value in schema.items():
                if key in {
                    "$defs",
                    "properties",
                    "type",
                    "title",
                    "required",
                    "$ref",
                    "$schema",
                }:
                    continue
                extra_info[key] = value
        return extra_info

    def resolve_schemas(self):
        schemas: Dict[str, Any] = {}
        for m in (self.request, self.response, self.params):
            if m is None:
                continue
            name, schema = extract_schema_info(m)
            schemas[name] = schema

        # Also include schemas declared in custom responses
        for _code, cfg in self.extra_responses.items():
            schema_model = cfg.get("schema") if isinstance(cfg, dict) else None
            if schema_model is not None:
                name, schema_def = extract_schema_info(schema_model)
                schemas[name] = schema_def
        return schemas

    def get_methods(self):
        # Methods resolution
        wrapper_methods = self.methods
        extras = self.extract_extras()

        if wrapper_methods:
            methods_list = [m.lower() for m in wrapper_methods]
        else:
            m_from_extra = (
                extras.get("methods")
                or extras.get("method")
                or extras.get("http_method")
            )
            if isinstance(m_from_extra, str):
                methods_list = [m_from_extra.lower()]
            elif isinstance(m_from_extra, (list, tuple)):
                methods_list = [str(m).lower() for m in m_from_extra]
            else:
                methods_list = ["post"]
        return methods_list

    def _parse_docstring(
        self,
        *,
        docstring: str,
        last_updated: Optional[datetime] = None,
        add_field_tables: bool = False,
        return_html: bool = True,
    ) -> Tuple[str | None, str | None]:
        """Parse view docstring into a summary and a description.

        Returns:
            A tuple of (summary, description). If no docstring is provided,
            both values will be None to avoid injecting empty fields in the
            top-level info object.
        """

        if not docstring:
            return None, None

        doc = inspect.cleandoc(docstring)
        lines = doc.splitlines()

        # Remove leading empty lines
        while lines and not lines[0].strip():
            lines.pop(0)
        if not lines:
            return None, None

        summary = lines[0].strip()
        rest = lines[1:]
        stop_tokens = {
            "args:",
            "arguments:",
            "parameters:",
            "returns:",
            "return:",
            "raises:",
            "examples:",
        }
        desc_lines: list[str] = []
        for ln in rest:
            if ln.strip().lower() in stop_tokens:
                break
            desc_lines.append(ln)

        view_doc = "\n".join(desc_lines).strip()
        if add_field_tables and conf.LAMINA_GENERATE_FIELD_TABLES_IN_DOCS:
            field_tables = self.get_field_tables()
            if field_tables:
                if view_doc:
                    view_doc += "\n\n"
                view_doc += field_tables
        if return_html:
            description = markdown_to_html(view_doc, last_updated)
        else:
            description = view_doc
        return summary, description

    def get_summary(self):
        extras = self.extract_extras()
        default_name = titlecase(self.get_path().replace("/", ""))
        return (
            self._parse_docstring(docstring=self.view_docstring)[0]
            or extras.get("summary")
            or default_name
        )

    def get_description(self):
        extras = self.extract_extras()
        return (
            self._parse_docstring(
                docstring=self.view_docstring,
                last_updated=self.file_last_update,
                add_field_tables=True,
            )[1]
            or extras.get("description")
            or ""
        )

    def _python_to_openapi_type(self, annotation: Any) -> str:
        """Map Python types to OpenAPI types."""
        if annotation in (int,):
            return "integer"
        if annotation in (float, Decimal):
            return "number"
        if annotation is bool:
            return "boolean"
        if annotation is str:
            return "string"
        if annotation is list or getattr(annotation, "__origin__", None) is list:
            return "array"
        if annotation is dict or getattr(annotation, "__origin__", None) is dict:
            return "object"
        if inspect.isclass(annotation) and issubclass(annotation, Enum):
            return "enum"
        if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
            return "object"
        return (
            annotation.__name__ if hasattr(annotation, "__name__") else str(annotation)
        ).lower()

    def _get_all_models(self) -> List[Tuple[Type[BaseModel | RootModel], str]]:
        """Recursively collect all Pydantic models used in the view."""
        models: List[Tuple[Type[BaseModel | RootModel], str]] = []
        seen: set[Type[BaseModel | RootModel]] = set()

        def collect(model: Type[BaseModel | RootModel], default_title: str):
            if model is None or not (
                inspect.isclass(model) and issubclass(model, (BaseModel, RootModel))
            ):
                return
            if model in seen:
                return
            seen.add(model)

            models.append((model, default_title))

            # Recurse into fields
            if hasattr(model, "model_fields"):
                for field in model.model_fields.values():
                    annotation = field.annotation
                    # Handle Optional, List, etc.
                    args = getattr(annotation, "__args__", [])

                    # Direct model
                    if inspect.isclass(annotation) and issubclass(
                        annotation, (BaseModel, RootModel)
                    ):
                        collect(
                            annotation, f"\n\n### {titlecase(annotation.__name__)}\n\n"
                        )

                    # Inside Generic (List[Model], etc.)
                    for arg in args:
                        if inspect.isclass(arg) and issubclass(
                            arg, (BaseModel, RootModel)
                        ):
                            collect(arg, f"\n\n### {titlecase(arg.__name__)}\n\n")

        collect(self.params, "\n\n## Query Parameters\n\n")
        collect(self.request, "\n\n## Request Body Fields\n\n")
        collect(self.response, "\n\n## Response Body Fields\n\n")

        # Add models from extra responses
        if self.extra_responses:
            for _code, cfg in self.extra_responses.items():
                schema_model = cfg.get("schema") if isinstance(cfg, dict) else None
                if schema_model:
                    collect(schema_model, f"\n\n### {schema_model.__name__}\n\n")

        return models

    def get_field_tables(self) -> str:
        description = ""

        for model, default_title in self._get_all_models():
            if model.__name__ == "RootModel":
                continue
            model_name, _ = extract_schema_info(model)
            fields = model.model_fields
            if fields:
                # Get Model Docstring
                model_docstring = model.__doc__
                doc_title, doc_description = self._parse_docstring(
                    docstring=model_docstring,
                    add_field_tables=False,
                    return_html=False,
                )
                title = f"\n\n## {doc_title}\n\n" if doc_title else default_title
                if not title:
                    title = f"\n\n## {titlecase(model.__name__)}\n\n"
                model_table = title
                if doc_description:
                    model_table += f"{doc_description}\n\n"
                model_table += (
                    "| Field | Type | Required | Default Value "
                    "| Description | Examples |\n"
                )
                model_table += (
                    "|-------|------|----------|---------------"
                    "|-------------|----------|\n"
                )
                required_fields = model.model_json_schema().get("required") or []
                for name, field in fields.items():
                    annotation = field.annotation
                    table_t = self._python_to_openapi_type(annotation)
                    is_required = (
                        name in required_fields or field.alias in required_fields
                    )
                    default_value = (
                        field.default
                        if field.default is not None
                        and field.default is not PydanticUndefined
                        else "--"
                    )
                    if isinstance(default_value, Enum):
                        default_value = default_value.value
                    elif isinstance(default_value, (datetime.date, datetime.datetime)):
                        default_value = default_value.isoformat()
                    elif isinstance(default_value, Decimal):
                        default_value = str(default_value)

                    desc = field.description or "--"

                    # Pydantic v2 examples can be in field.examples or json_schema_extra
                    examples = (
                        getattr(field, "examples", None)
                        or (field.json_schema_extra or {}).get("examples")
                        or []
                    )
                    examples_str = (
                        ", ".join(str(ex) for ex in examples) if examples else "--"
                    )
                    model_table += (
                        f"| {field.alias or name} | {table_t} | "
                        f"{'Yes' if is_required else 'No'} | "
                        f"{default_value} | {desc} | {examples_str} |\n"
                    )
                description += model_table
        return description

    def get_path(self):
        # Check for path in view first
        path = None
        if self.path:
            path = self.path
        if not path:
            # Example: foo.bar.handler
            import_parts = self.import_path.split(".")
            index = None
            match conf.LAMINA_USE_OBJECT_NAME:
                case "package":
                    index = -3
                case "module":
                    index = -2
                case "function":
                    index = -1
                case _:
                    raise ValueError(
                        "Invalid value for LAMINA_USE_OBJECT_NAME. "
                        "Expected one of: package, module, function."
                    )
            path = import_parts[index if len(import_parts) >= abs(index) else index + 1]
            path = kebabcase(path)
        return f"/{path}" if not path.startswith("/") else path

    def get_operation_id(self):
        extras = self.extract_extras()
        fallback_name = camelcase(self.get_path().replace("/", ""))
        return extras.get("operationId", fallback_name)

    def get_parameters(self) -> List[ParameterObject]:
        """Convert a Pydantic model into OpenAPI query parameters."""
        params: List[ParameterObject] = []
        if self.params is None:
            return params

        # Only handle BaseModel subclasses for parameters
        if inspect.isclass(self.params) and issubclass(self.params, BaseModel):
            for name, field in self.params.model_fields.items():
                annotation = field.annotation
                # Minimal type mapping
                t: str = "string"
                if annotation in (int, float):
                    t = "number" if annotation is float else "integer"
                elif annotation is bool:
                    t = "boolean"

                required_fields = self.params.model_json_schema().get("required") or []
                is_required = name in required_fields or field.alias in required_fields
                desc = field.description or ""
                params.append(
                    ParameterObject(
                        **{
                            "name": field.alias or name,
                            "in": "query",
                            "required": is_required,
                            "schema": {"type": t},
                            "description": desc,
                        }
                    )
                )
        return params

    @staticmethod
    def get_model_schema(
        model: Optional[Type[BaseModel | RootModel]],
    ) -> Optional[dict]:
        if model is None:
            return None
        name, _ = extract_schema_info(model)
        return {
            "application/json": {"schema": {"$ref": f"#/components/schemas/{name}"}}
        }

    def get_tags(self) -> List[str]:
        extras = self.extract_extras()
        tags = self.tags or extras.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        return tags
