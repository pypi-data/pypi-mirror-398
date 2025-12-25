from pydantic import BaseModel
from typing import Any

class SqlQueryRequest(BaseModel):
    """The SQL query request.
    
    Response fields are not supported for this request, use appropriate SQL query to get the desired fields.
    """
    query: str
    variables: dict[str, Any] | None
