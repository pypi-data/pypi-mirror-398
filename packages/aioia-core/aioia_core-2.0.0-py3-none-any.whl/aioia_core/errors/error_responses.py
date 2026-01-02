"""Error response models and utility functions for FastAPI applications."""

from typing import Any, cast

from fastapi import HTTPException
from pydantic import BaseModel, Field

from aioia_core.errors import error_codes


class ErrorResponse(BaseModel):
    """
    Standardized error response model following RFC 9457 Problem Details for HTTP APIs.
    This model provides consistent error information across all FastAPI endpoints.
    """

    status: int = Field(
        ...,
        description="HTTP status code",
    )
    detail: str = Field(
        ...,
        description="Human-readable error message",
    )
    code: str = Field(
        ...,
        description="Machine-readable error code for client-side error handling",
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "status": 401,
                    "detail": "Invalid authentication credentials",
                    "code": "INVALID_TOKEN",
                },
                {
                    "status": 404,
                    "detail": "Resource not found: item_123",
                    "code": "RESOURCE_NOT_FOUND",
                },
                {
                    "status": 422,
                    "detail": "Validation error in field 'email': Invalid email format",
                    "code": "VALIDATION_ERROR",
                },
            ]
        }


def extract_error_code_from_exception(exc: HTTPException) -> str:
    """
    HTTPException에서 에러 코드를 추출합니다.
    detail이 dict 형태인 경우 code 필드를 찾고, 없으면 기본값 반환

    Args:
        exc: HTTPException 인스턴스

    Returns:
        str: 에러 코드
    """
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return cast(dict[str, Any], exc.detail)["code"]

    # 상태 코드별 기본 에러 코드 매핑
    default_codes = {
        401: error_codes.UNAUTHORIZED,
        403: error_codes.FORBIDDEN,
        404: error_codes.RESOURCE_NOT_FOUND,
        422: error_codes.VALIDATION_ERROR,
        500: error_codes.INTERNAL_SERVER_ERROR,
    }

    return default_codes.get(exc.status_code, error_codes.INTERNAL_SERVER_ERROR)


def get_error_detail_from_exception(exc: HTTPException) -> str:
    """
    HTTPException에서 에러 상세 메시지를 추출합니다.

    Args:
        exc: HTTPException 인스턴스

    Returns:
        str: 에러 상세 메시지
    """
    if isinstance(exc.detail, dict) and "detail" in exc.detail:
        return cast(dict[str, Any], exc.detail)["detail"]
    if isinstance(exc.detail, str):
        return exc.detail
    return str(exc.detail)
