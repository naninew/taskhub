# [Ngày 1] Các custom exception cho ứng dụng


class TaskHubException(Exception):
    """Base exception class cho toàn bộ ứng dụng TaskHub."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ResourceNotFoundError(TaskHubException):
    """Exception khi không tìm thấy tài nguyên."""
    pass


class DuplicateResourceError(TaskHubException):
    """Exception khi tài nguyên bị trùng lặp."""
    pass
