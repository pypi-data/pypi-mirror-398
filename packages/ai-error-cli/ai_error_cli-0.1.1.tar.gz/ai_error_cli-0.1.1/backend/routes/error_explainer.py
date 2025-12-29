from fastapi import APIRouter
# from backend.schemas.error_schema import ErrorRequest, ErrorResponse
# from backend.services.ai_service import explain_error
from schemas.error_schema import ErrorRequest, ErrorResponse
from services.ai_service import explain_error

router = APIRouter()

@router.post("/explain-error", response_model=ErrorResponse)
def explain_error_route(request: ErrorRequest):
    return explain_error(request.error)
