from rest_framework_simplejwt.models import TokenUser
from rest_framework_simplejwt.tokens import Token


class JWTUser(TokenUser):

    def __init__(self, token: "Token"):
        super().__init__(token)
        self.phone = self.token.get("phone")
        self._groups = self.token.get("groups")
        self.should_cache_requests = self.token.get("should_cache_requests")
