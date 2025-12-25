from typing import Any, Dict, List, TypedDict


class OpenAPIContactObject(TypedDict, total=False):
    name: str
    url: str
    email: str


class OpenAPILicenseObject(TypedDict, total=False):
    name: str
    url: str


class OpenAPIInfoObject(TypedDict, total=False):
    title: str
    version: str
    summary: str
    description: str
    termsOfService: str
    contact: OpenAPIContactObject
    license: OpenAPILicenseObject


class OpenAPIServerVariableObject(TypedDict, total=False):
    enum: List[str]
    default: str
    description: str


class OpenAPIServerObject(TypedDict, total=False):
    url: str
    description: str
    variables: OpenAPIServerVariableObject


class RequestBodyObject(TypedDict, total=False):
    content: Dict[str, Any]
    required: bool
    description: str


class ResponseObject(TypedDict, total=False):
    description: str | Any | None
    content: Dict[str, Any]


class ParameterObject(TypedDict, total=False):
    name: str
    in_: str
    required: bool
    schema: Dict[str, Any]
    description: str


class OperationObject(TypedDict, total=False):
    summary: str | Any | None
    description: str
    tags: List[str]
    operationId: str
    parameters: List[ParameterObject]
    requestBody: RequestBodyObject
    responses: Dict[str, ResponseObject]


class ComponentsObject(TypedDict, total=False):
    schemas: Dict[str, Any]
    securitySchemes: Dict[str, Any]


class OpenAPIExternalDocumentationObject(TypedDict, total=False):
    description: str
    url: str


class OpenAPIPathItemObject(TypedDict, total=False):
    get: OperationObject
    put: OperationObject
    post: OperationObject
    delete: OperationObject
    options: OperationObject
    head: OperationObject
    patch: OperationObject
    trace: OperationObject


class OpenAPITagsObject(TypedDict, total=False):
    name: str
    description: str
    externalDocs: OpenAPIExternalDocumentationObject


class OpenAPIObject(TypedDict, total=False):
    openapi: str
    info: OpenAPIInfoObject
    jsonSchemaDialect: str
    servers: List[OpenAPIServerObject]
    paths: Dict[str, Dict[str, OperationObject]]
    webhooks: Dict[str, OpenAPIPathItemObject]
    components: ComponentsObject
    security: List[Dict[str, List[str]]]
    tags: List[OpenAPITagsObject]
    externalDocs: OpenAPIExternalDocumentationObject
