import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UppercaseValidator:
    """Password must contain at least one uppercase letter."""

    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _('Пароль должен содержать хотя бы одну заглавную букву.'),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _('Пароль должен содержать хотя бы одну заглавную букву.')


class SpecialCharValidator:
    """Password must contain at least one special character."""

    SPECIAL_CHARS = r'[!@#$%^&*()_+\-=\[\]{};\'\\:"|,.<>\/?]'

    def validate(self, password, user=None):
        if not re.search(self.SPECIAL_CHARS, password):
            raise ValidationError(
                _('Пароль должен содержать хотя бы один специальный символ: !@#$%^&*...'),
                code='password_no_special',
            )

    def get_help_text(self):
        return _('Пароль должен содержать хотя бы один специальный символ.')
