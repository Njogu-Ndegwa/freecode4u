# myproject/auth_backends.py
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        # "username" will actually be the email in this approach
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None
        
        if user.check_password(password) and user.is_active:
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
