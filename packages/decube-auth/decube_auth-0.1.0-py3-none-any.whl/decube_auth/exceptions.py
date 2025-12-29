class DecubeError(Exception):
    pass


class AuthenticationError(DecubeError):
    pass


class ConflictError(DecubeError):
    pass


class BadRequestError(DecubeError):
    pass


class ServerError(DecubeError):
    pass
