
class DomainError(Exception):
    code = "domain_error"
    status_code = 400
    message = "The operation could not be completed."


class EmailAlreadyRegisteredError(DomainError):
    code = "email_already_registered"
    status_code = 409
    message = "This email is already registered."


class InvalidCredentialsError(DomainError):
    code = "invalid_credentials"
    status_code = 401
    message = "Invalid email or password."


class ProjectNotFoundError(DomainError):
    code = "project_not_found"
    status_code = 404
    message = "Project not found."


class TaskNotFoundError(DomainError):
    code = "task_not_found"
    status_code = 404
    message = "Task not found."


class NotAuthorizedError(DomainError):
    code = "not_authorized"
    status_code = 403
    message = "You do not have permission to access this resource."
