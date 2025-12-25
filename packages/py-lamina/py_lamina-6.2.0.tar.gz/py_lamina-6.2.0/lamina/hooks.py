from __future__ import annotations

from typing import Any, Dict, Optional, Union


def pre_parse(
    event: Union[Dict[str, Any], bytes, str], context: Optional[Dict[str, Any]]
) -> Union[Dict[str, Any], bytes, str]:
    """Default no-op pre-parse hook.

    Called after receiving the raw event/context but before input parsing/validation.
    Should return the (possibly modified) event.
    """

    return event


def pre_execute(
    request: Any,
    event: Union[Dict[str, Any], bytes, str],
    context: Optional[Dict[str, Any]],
) -> Any:
    """Default no-op pre-execute hook.

    Called with the Request, original event and context before executing the handler.
    Should return the (possibly modified) Request.
    """

    return request


def pos_execute(response: Any, request: Any) -> Any:
    """Default no-op post-execute hook.

    Called with the handler raw response and the Request,
    before output schema serialization.
    Should return the (possibly modified) response.
    """

    return response


def pre_response(body: Any) -> Any:
    """Default no-op pre-response hook.

    Called with the response body at the end
    of try/except block, just before returning.
    Should return the (possibly modified) body.
    """

    return body
