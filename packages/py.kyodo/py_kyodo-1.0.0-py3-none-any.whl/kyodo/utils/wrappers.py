from .exceptions import NeedAuthError


def require_auth(func):
    def wrapper(self, *args, **kwargs):
        if not getattr(self, "auth_token", ""):
            raise NeedAuthError(
                {"message": "You need to be authorized to use this method"}
            )
        return func(self, *args, **kwargs)

    return wrapper
