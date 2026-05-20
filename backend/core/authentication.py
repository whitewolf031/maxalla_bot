from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings


class FakeUser:
    """Internal API user placeholder"""
    is_authenticated = True
    is_active = True

    def __str__(self):
        return "InternalAPIUser"


class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return None
        if api_key != settings.BACKEND_API_KEY:
            raise AuthenticationFailed('Invalid API Key')
        return (FakeUser(), None)
