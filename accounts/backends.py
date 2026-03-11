from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Authenticate using email + password instead of username + password.
    Checks is_active and is_approved before granting access.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get('email', username)
        if not email or not password:
            return None

        email = email.strip().lower()

        try:
            user = User.objects.select_related('department').get(email=email)
        except User.DoesNotExist:
            # Run the default password hasher to prevent timing attacks
            User().set_password(password)
            return None

        if not user.check_password(password):
            return None

        if not self.user_can_authenticate(user):
            return None

        return user

    def user_can_authenticate(self, user):
        """Only active AND approved users can log in."""
        return bool(user.is_active and user.is_approved)
