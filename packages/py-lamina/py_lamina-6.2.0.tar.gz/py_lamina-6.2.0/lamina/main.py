import asyncio
import functools
import inspect
import json
import os
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Optional,
    Type,
    TypedDict,
    TypeVar,
    Union,
)

import magic
from loguru import logger
from pydantic import BaseModel, RootModel, ValidationError

from lamina import conf
from lamina.helpers import DecimalEncoder

# Global registry of lamina-decorated handlers (wrappers)
LAMINA_REGISTRY: list[Callable[..., Any]] = []

SchemaType = TypeVar("SchemaType", bound=BaseModel | RootModel)


@dataclass
class Request(Generic[SchemaType]):
    """Request object passed to decorated handlers.

    Attributes:
        data: Parsed body or model instance according to schema_in and flags.
        event: Original AWS Lambda event.
        context: Lambda context object.
        query: Optional parsed query parameters if params_in schema is provided.
    """

    data: Union[SchemaType, str]
    event: Union[Dict[str, Any], bytes, str]
    context: Optional[Dict[str, Any]]
    headers: Optional[Dict[str, Any]]
    query: Optional[BaseModel] = None


class ResponseDict(TypedDict):
    statusCode: int
    headers: Dict[str, str]
    body: str


def lamina(
    path: Optional[str] = None,
    schema_in: Optional[Type[SchemaType]] = None,
    schema_out: Optional[Type[BaseModel] | Type[RootModel]] = None,
    params_in: Optional[Type[BaseModel] | Type[RootModel]] = None,
    accepts: str = "application/json; charset=utf-8",
    produces: str | None = None,
    step_functions: bool = False,
    responses: Optional[Dict[int, Dict[str, Any]]] = None,
    add_to_spec: bool = True,
    methods: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., ResponseDict]]:
    def decorator(f: Callable[..., Any]) -> Callable[..., ResponseDict]:
        @functools.wraps(f)
        def wrapper(
            event: Dict[str, Any] | bytes | str,
            context: Optional[Dict[str, Any]],
            *args: Any,
            **kwargs: Any,
        ) -> ResponseDict:
            if f.__doc__:
                title = f.__doc__.split("\n")[0].strip()
            else:
                # event may not be a dict; guard get
                path = event.get("path") if isinstance(event, dict) else "unknown"
                title = f"{f.__name__} for path {path}"
            logger.info(f"******* {title.upper()} *******")

            magic_content_type = "application/json"

            try:
                # Run pre-parse hook (may adjust event)
                pre_parse_hook = conf.LAMINA_PRE_PARSE_CALLBACK
                if inspect.iscoroutinefunction(pre_parse_hook):
                    event = asyncio.run(pre_parse_hook(event, context))
                else:
                    event = pre_parse_hook(event, context)

                # Parse Headers
                headers = event.get("headers", {}) if isinstance(event, dict) else {}
                if headers is None:
                    headers = {}

                # Parse Params if schema provided
                query_info = None
                if params_in:
                    query_data = (
                        event.get("queryStringParameters", {})
                        if isinstance(event, dict)
                        else {}
                    )
                    query_info = params_in(**query_data)

                # Parse input (after possible pre-parse modification)
                if schema_in is None:
                    data = (
                        event["body"]
                        if (isinstance(event, dict) and not step_functions)
                        else event
                    )
                else:
                    # First check if is Base64 encoded
                    is_base64 = (
                        event.get("isBase64Encoded", False)
                        if isinstance(event, dict)
                        else False
                    )
                    if is_base64:
                        logger.debug(
                            f"Body received is base64 encoded, "
                            f"passing raw and run {schema_in.__name__}..."
                        )
                        decoded_body = (
                            event["body"]
                            if (isinstance(event, dict) and not step_functions)
                            else event
                        )
                        data = schema_in(decoded_body)
                    else:
                        try:
                            # Try to parse body as JSON first
                            request_body = (
                                json.loads(event["body"])
                                if (isinstance(event, dict) and not step_functions)
                                else event
                            )
                            logger.debug(
                                f"Body received is JSON, "
                                f"parsing and run {schema_in.__name__}..."
                            )
                            data = schema_in(**request_body)
                        except (json.JSONDecodeError, TypeError):
                            # Fallback: pass raw body to schema
                            logger.debug(
                                f"Body received is not JSON, "
                                f"passing raw and run {schema_in.__name__}..."
                            )
                            request_body = event
                            data = schema_in(request_body)

                # Build initial Request and run pre-execute hook
                request = Request(
                    data=data,
                    event=event,
                    context=context,
                    query=query_info,
                    headers=headers,
                )
                pre_execute_hook = conf.LAMINA_PRE_EXECUTE_CALLBACK
                if inspect.iscoroutinefunction(pre_execute_hook):
                    request = asyncio.run(pre_execute_hook(request, event, context))
                else:
                    request = pre_execute_hook(request, event, context)

                status_code = 200

                headers: Dict[str, str] = {}

                # check if function is a coroutine
                if inspect.iscoroutinefunction(f):
                    response: Any = asyncio.run(f(request))
                else:
                    response = f(request)

                # Execute post-execution hook on raw response (before schema_out)
                pos_execute_hook = conf.LAMINA_POS_EXECUTE_CALLBACK
                if inspect.iscoroutinefunction(pos_execute_hook):
                    response = asyncio.run(pos_execute_hook(response, request))
                else:
                    response = pos_execute_hook(response, request)

                if isinstance(response, tuple):
                    status_code = response[1]
                    if len(response) == 3:
                        headers = response[2]
                    response = response[0]

                try:
                    body: str | Any = response
                    if body:
                        if schema_out:
                            if issubclass(schema_out, RootModel):
                                root = schema_out(response).root
                                if root is not None:
                                    body = (
                                        schema_out(response).model_dump_json(
                                            by_alias=True
                                        )
                                        if not isinstance(root, str)
                                        else root
                                    )
                            else:
                                body = schema_out(**response).model_dump_json(
                                    by_alias=True
                                )
                        body = (
                            json.dumps(body, cls=DecimalEncoder)
                            if not isinstance(body, str)
                            else body
                        )
                    magic_content_type = (
                        magic.from_buffer(body, mime=True) if body else "text/html"
                    )
                except Exception as e:
                    # This is an Internal Server Error
                    logger.error(f"Error when attempt to serialize response: {e}")
                    status_code = 500
                    body = json.dumps(
                        [
                            {
                                "field": (
                                    schema_out.__name__ if schema_out else "DumpJson"
                                ),
                                "message": str(e),
                            }
                        ],
                        cls=DecimalEncoder,
                    )

                full_headers: Dict[str, str] = {
                    "Content-Type": produces or f"{magic_content_type}; charset=utf-8",
                }
                if headers:
                    full_headers.update(headers)

                # Run pre-response hook just before returning
                pre_response_hook = conf.LAMINA_PRE_RESPONSE_CALLBACK
                if inspect.iscoroutinefunction(pre_response_hook):
                    body = asyncio.run(pre_response_hook(body))  # type: ignore[misc]
                else:
                    body = pre_response_hook(body)

                return {
                    "statusCode": status_code,
                    "headers": full_headers,
                    "body": body,  # type: ignore[return-value]
                }
            except ValidationError as e:
                messages = [
                    {
                        "field": (
                            error["loc"][0] if error.get("loc") else "ModelValidation"
                        ),
                        "message": error["msg"],
                    }
                    for error in e.errors()
                ]
                logger.error(messages)
                body = json.dumps({conf.LAMINA_DEFAULT_ERROR_KEY: messages})
                return {
                    "statusCode": 422,
                    "body": body,
                    "headers": {
                        "Content-Type": "application/json; charset=utf-8",
                    },
                }
            except (ValueError, TypeError) as e:
                message = f"Error when attempt to read received event: {e}."
                logger.error(str(e))
                logger.exception(e)
                body = json.dumps({conf.LAMINA_DEFAULT_ERROR_KEY: message})
                return {
                    "statusCode": 400,
                    "body": body,
                    "headers": {
                        "Content-Type": "application/json; charset=utf-8",
                    },
                }
            except Exception as e:
                logger.exception(e)
                body = json.dumps({conf.LAMINA_DEFAULT_ERROR_KEY: str(e)})
                return {
                    "statusCode": 500,
                    "body": body,
                    "headers": {
                        "Content-Type": "application/json; charset=utf-8",
                    },
                }

        # We need to find the python file which contains the decorated function
        # and get the last update time to include in the description.
        fn_file = inspect.getfile(f)
        try:
            last_updated = os.path.getmtime(fn_file)
            wrapper.last_updated = last_updated
        except Exception:
            wrapper.last_updated = None

        wrapper.schema_in = schema_in
        wrapper.schema_out = schema_out
        wrapper.request_content_type = accepts
        wrapper.response_content_type = produces
        wrapper.params_in = params_in
        wrapper.path = path
        wrapper.responses = responses or {}
        wrapper.methods = methods
        wrapper.tags = tags
        wrapper.import_path = f"{f.__module__}.{f.__name__}"

        # Register wrapper for OpenAPI generation
        if add_to_spec:
            try:
                LAMINA_REGISTRY.append(wrapper)
            except Exception:
                # Fallback: do not break if registry fails for some reason
                logger.debug("Unable to register lamina wrapper in registry.")

        return wrapper

    return decorator
