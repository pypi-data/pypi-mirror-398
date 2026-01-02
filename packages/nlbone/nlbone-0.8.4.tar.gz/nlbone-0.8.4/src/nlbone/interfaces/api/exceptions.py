from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: int | str = 0
    message: Optional[str] = None
    fields: Optional[Union[List[Union[str, int]], str]] = None
    data: Optional[Union[List[Dict], Dict]] = None


class BaseHttpException(HTTPException):
    def __init__(
            self,
            status_code: int,
            detail: Optional[str] = None,
            errors: Optional[List[ErrorDetail]] = None,
            fields: Optional[Union[List[Union[str, int]], str]] = None,
            data: Optional[Dict] = None,
            code: Optional[str] = None,
    ):
        if errors is None:
            message = detail or HTTPStatus(status_code).phrase

            if not code:
                code = HTTPStatus(status_code).phrase.lower().replace(" ", "_")

            errors = [
                ErrorDetail(
                    code=code,
                    message=message,
                    fields=fields,
                    data=data
                )
            ]

        self.errors = errors
        super().__init__(status_code=status_code, detail=self.message)

    @property
    def message(self) -> str:
        if self.errors and self.errors[0].message:
            return self.errors[0].message
        return HTTPStatus(self.status_code).phrase


class UnprocessableEntityException(BaseHttpException):
    def __init__(
            self,
            detail: str = None,
            fields: Optional[Union[List[Union[str, int]], str]] = None,
            validation_errors: Optional[List[Dict[str, Any]]] = None
    ):
        errors = None

        if validation_errors:
            errors = []
            for error in validation_errors:
                err_type = error.get("type")
                loc = error.get("loc")
                msg = error.get("msg")
                inp = error.get("input")

                if err_type == "json_invalid":
                    loc = ["body"]
                    msg = "Invalid JSON format. Please check your syntax (e.g., convert '۱' to '1')."

                elif isinstance(loc, tuple):
                    loc = list(loc)

                error_data = {}
                if inp is not None and not (isinstance(inp, dict) and not inp):
                    error_data["input"] = inp

                errors.append(
                    ErrorDetail(
                        code=err_type or "validation_error",
                        message=msg,
                        fields=loc,
                        data=error_data if error_data else None
                    )
                )

        super().__init__(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=detail,
            fields=fields,
            errors=errors
        )


class BadRequestException(BaseHttpException):
    def __init__(self, detail: str = None, code: int = 0):
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=detail, code=code)


class UnauthorizedException(BaseHttpException):
    def __init__(self, detail: str = None):
        super().__init__(status_code=HTTPStatus.UNAUTHORIZED, detail=detail)


class ForbiddenException(BaseHttpException):
    def __init__(self, detail: str = None):
        super().__init__(status_code=HTTPStatus.FORBIDDEN, detail=detail)


class NotFoundException(BaseHttpException):
    def __init__(self, detail: str = None):
        super().__init__(status_code=HTTPStatus.NOT_FOUND, detail=detail)


class ConflictException(BaseHttpException):
    def __init__(self, detail: str = None, data: Optional[Union[List[Dict], Dict]] = None):
        super().__init__(status_code=HTTPStatus.CONFLICT, detail=detail, data=data)


class NotSupportedException(BaseHttpException):
    def __init__(self, detail: str = None):
        super().__init__(status_code=HTTPStatus.NOT_IMPLEMENTED, detail=detail)


class InternalServerException(BaseHttpException):
    def __init__(self, detail: str = None):
        super().__init__(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=detail)


class LogicalValidationException(UnprocessableEntityException):
    def __init__(self, detail: str = None,
                 fields: Optional[Union[List[str], str]] = None,
                 validation_errors: Optional[List[Dict[str, Any]]] = None):
        super().__init__(
            detail=detail,
            fields=fields,
            validation_errors=validation_errors
        )


class GoneException(BaseHttpException):
    def __init__(self, detail: str = None):
        super().__init__(status_code=HTTPStatus.GONE, detail=detail)


class TooManyRequestsException(BaseHttpException):
    def __init__(self, detail: str = None):
        super().__init__(status_code=HTTPStatus.TOO_MANY_REQUESTS, detail=detail)


class NotAcceptableException(BaseHttpException):
    def __init__(self, detail: str = None):
        super().__init__(status_code=HTTPStatus.NOT_ACCEPTABLE, detail=detail)
