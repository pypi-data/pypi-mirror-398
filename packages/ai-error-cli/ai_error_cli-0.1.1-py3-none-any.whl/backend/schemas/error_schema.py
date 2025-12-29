from pydantic import BaseModel
from typing import List

class ErrorRequest(BaseModel):
    error: str

class ErrorResponse(BaseModel):
    cause: str
    solutions: List[str] = []
    example: str
    error_type: str
    confidence: float
    possible_fix_steps: List[str] = []
    references: List[str] = []
    preventive_tips: List[str] = []
    code_context: str