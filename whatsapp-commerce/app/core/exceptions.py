class AppError(Exception):
    """Base exception for application errors."""
    def __init__(self, message, status_code=400, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self):
        rv = {"error": self.message}
        if self.details:
            rv["details"] = self.details
        return rv


class ResourceNotFoundError(AppError):
    def __init__(self, message="Resource not found", details=None):
        super().__init__(message=message, status_code=404, details=details)


class ValidationError(AppError):
    def __init__(self, message="Invalid data provided", details=None):
        super().__init__(message=message, status_code=400, details=details)


class TenantViolationError(AppError):
    def __init__(self, message="Cross-tenant access violation", details=None):
        super().__init__(message=message, status_code=403, details=details)


class PermissionDeniedError(AppError):
    def __init__(self, message="Insufficient permissions", details=None):
        super().__init__(message=message, status_code=403, details=details)


class ConflictError(AppError):
    def __init__(self, message="Resource conflict", details=None):
        super().__init__(message=message, status_code=409, details=details)
