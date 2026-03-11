from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer:
    - Uses email as login field
    - Adds user info claims to the token payload
    - Checks is_approved before issuing token
    """

    username_field = 'email'

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Custom claims embedded in the JWT payload
        token['email'] = user.email
        token['full_name'] = user.full_name
        token['role'] = user.role
        token['department'] = user.department.name if user.department else None
        token['is_approved'] = user.is_approved

        return token

    def validate(self, attrs):
        # Normalise email
        attrs[self.username_field] = attrs.get(self.username_field, '').strip().lower()
        data = super().validate(attrs)

        if not self.user.is_approved:
            raise AuthenticationFailed(
                'Аккаунт ожидает подтверждения администратором.',
                code='not_approved',
            )

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.display_name', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'full_name', 'role', 'position',
            'phone', 'department', 'department_name',
            'is_approved', 'two_factor_enabled', 'date_joined',
        )
        read_only_fields = ('id', 'email', 'role', 'is_approved', 'date_joined')


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=10)
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password2': 'Пароли не совпадают.'})
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный текущий пароль.')
        return value
