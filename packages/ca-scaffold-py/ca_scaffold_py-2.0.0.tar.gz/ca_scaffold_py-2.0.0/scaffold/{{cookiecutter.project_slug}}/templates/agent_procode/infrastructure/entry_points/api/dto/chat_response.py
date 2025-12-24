
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ChatResponse(BaseModel):
    response: Optional[Dict[str, Any]]