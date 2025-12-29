from rest_framework_simplejwt.authentication import JWTAuthentication


class Authentication(JWTAuthentication):

    def authenticate(self, request):
        if (
            request
            and request.path
            and (
                request.path.startswith("/swagger")
                or request.path.startswith("/redoc")
                or request.path.startswith("/docs")
            )
        ):
            return None

        return super().authenticate(request)
