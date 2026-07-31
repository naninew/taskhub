# [Ngày 1] Các custom exception cho ứng dụng
# [Ngày 4] AppException base + handler JSON thống nhất {code, message, detail}


class TaskHubException(Exception):
    """Base exception class cho toàn bộ ứng dụng TaskHub (Ngày 1)."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ResourceNotFoundError(TaskHubException):
    """Exception khi không tìm thấy tài nguyên (Ngày 1)."""

    pass


class DuplicateResourceError(TaskHubException):
    """Exception khi tài nguyên bị trùng lặp (Ngày 1)."""

    pass


class AppException(Exception):
    """[Ngày 4] Base exception — global handler trả JSON {code, message, detail}."""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        detail: str | None = None,
        status_code: int = 500,
    ) -> None:
        self.message = message
        self.code = code or self.__class__.__name__
        self.detail = detail if detail is not None else message
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(AppException):
    """[Ngày 4] HTTP 404 — tài nguyên không tồn tại."""

    def __init__(
        self,
        message: str = "Resource not found",
        *,
        code: str = "NOT_FOUND",
        detail: str | None = None,
    ) -> None:
        super().__init__(message, code=code, detail=detail, status_code=404)


class ForbiddenException(AppException):
    """[Ngày 4] HTTP 403 — không đủ quyền truy cập."""

    def __init__(
        self,
        message: str = "Forbidden",
        *,
        code: str = "FORBIDDEN",
        detail: str | None = None,
    ) -> None:
        super().__init__(message, code=code, detail=detail, status_code=403)


class ConflictException(AppException):
    """[Ngày 4] HTTP 409 — xung đột nghiệp vụ (vd: xoá OWNER cuối cùng)."""

    def __init__(
        self,
        message: str = "Conflict",
        *,
        code: str = "CONFLICT",
        detail: str | None = None,
    ) -> None:
        super().__init__(message, code=code, detail=detail, status_code=409)


class UnauthorizedException(AppException):
    """[Ngày 4] HTTP 401 — chưa xác thực hoặc token không hợp lệ."""

    def __init__(
        self,
        message: str = "Unauthorized",
        *,
        code: str = "UNAUTHORIZED",
        detail: str | None = None,
    ) -> None:
        super().__init__(message, code=code, detail=detail, status_code=401)
