from __future__ import annotations

from typing import Any, Mapping, Optional, List
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi import HTTPException as FastAPIHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_422_UNPROCESSABLE_ENTITY

from nlbone.adapters.i18n import translator as _
from .exceptions import BaseHttpException, ErrorDetail, UnprocessableEntityException


class ErrorResponse(BaseModel):
    message: str
    errors: List[ErrorDetail]


def _ensure_trace_id(request: Request) -> str:
    rid = request.headers.get("X-Request-Id") or request.headers.get("X-Trace-Id")
    return rid or str(uuid4())


def _json_response(
        request: Request,
        status_code: int,
        content: Any,
        trace_id: Optional[str] = None,
        headers: Optional[Mapping[str, str]] = None,
) -> JSONResponse:
    tid = trace_id or _ensure_trace_id(request)

    if isinstance(content, dict):
        payload = content
    else:
        payload = content.model_dump(exclude_none=True) if hasattr(content, "model_dump") else content

    payload["trace_id"] = tid

    base_headers = {"X-Trace-Id": tid}
    if headers:
        base_headers.update(headers)

    return JSONResponse(
        status_code=status_code,
        content=payload,
        headers=base_headers
    )


def install_exception_handlers(
        app: FastAPI,
        *,
        logger: Any = None,
        expose_server_errors: bool = False,
) -> None:
    async def _log_exception(
            request: Request,
            exc: Exception,
            level: str = "warning",
            extra: Optional[dict] = None
    ):
        if not logger:
            return

        log_payload = {
            "path": request.url.path,
            "method": request.method,
            **extra
        } if extra else {"path": request.url.path}

        log_method = getattr(logger, level, logger.warning)
        log_method(str(exc), extra=log_payload)

    @app.exception_handler(BaseHttpException)
    async def _handle_base_http_exception(request: Request, exc: BaseHttpException):
        await _log_exception(request, exc, extra={"status": exc.status_code, "detail": exc.message})

        locale = getattr(request.state, "locale", None)

        main_message = _(exc.message, locale=locale)

        translated_errors = []
        if exc.errors:
            for err in exc.errors:
                err_copy = err.model_copy()
                if err_copy.message:
                    err_copy.message = _(err_copy.message, locale=locale)
                translated_errors.append(err_copy)

        response_model = ErrorResponse(
            message=main_message,
            errors=translated_errors
        )

        return _json_response(request, exc.status_code, content=response_model)

    @app.exception_handler(RequestValidationError)
    async def _handle_request_validation_error(request: Request, exc: RequestValidationError):
        await _log_exception(request, exc, level="info", extra={"errors": exc.errors()})

        normalized_exception = UnprocessableEntityException(
            detail="Validation Error",
            validation_errors=exc.errors()
        )
        return await _handle_base_http_exception(request, normalized_exception)

    @app.exception_handler(ValidationError)
    async def _handle_pydantic_validation_error(request: Request, exc: ValidationError):
        await _log_exception(request, exc, level="info", extra={"errors": exc.errors()})

        normalized_exception = UnprocessableEntityException(
            detail="Validation Error",
            validation_errors=exc.errors()
        )
        return await _handle_base_http_exception(request, normalized_exception)

    @app.exception_handler(StarletteHTTPException)
    async def _handle_starlette_http_exception(request: Request, exc: StarletteHTTPException):
        await _log_exception(request, exc, extra={"status": exc.status_code})

        locale = getattr(request.state, "locale", None)
        message_str = str(exc.detail) if exc.detail else "HTTP Error"
        translated_message = _(message_str, locale=locale)

        error_detail = ErrorDetail(
            code=exc.status_code,
            message=translated_message
        )

        response_model = ErrorResponse(
            message=translated_message,
            errors=[error_detail]
        )

        return _json_response(request, exc.status_code, content=response_model)

    @app.exception_handler(Exception)
    async def _handle_unexpected_exception(request: Request, exc: Exception):
        tid = _ensure_trace_id(request)
        await _log_exception(request, exc, level="exception", extra={"trace_id": tid})

        raw_detail = str(exc) if expose_server_errors else "Internal Server Error"
        locale = getattr(request.state, "locale", None)
        translated_detail = _(raw_detail, locale=locale)

        error_detail = ErrorDetail(
            code=HTTP_500_INTERNAL_SERVER_ERROR,
            message=translated_detail
        )

        response_model = ErrorResponse(
            message=translated_detail,
            errors=[error_detail]
        )

        return _json_response(
            request,
            HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_model,
            trace_id=tid
        )