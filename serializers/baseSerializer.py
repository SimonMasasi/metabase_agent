from ninja import Schema
from typing import Optional


class ResultsSchema(Schema):
    analysis: str
    error: Optional[str] = None