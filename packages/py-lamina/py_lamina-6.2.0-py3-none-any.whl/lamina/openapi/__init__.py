from typing import TypedDict

from pydantic import BaseModel


class ExtraResponsesDict(TypedDict):
    description: str
    schema: BaseModel
