from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class RegisterForm(forms.ModelForm):
    """
    Упрощённая форма регистрации.
    Пользователь вводит только: имя, фамилию, email и пароль.
    Роль, отдел и доступ назначает администратор после одобрения.
    """

    first_name = forms.CharField(
        label='Имя',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Иван',
            'autocomplete': 'given-name',
        }),
    )
    last_name = forms.CharField(
        label='Фамилия',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Иванов',
            'autocomplete': 'family-name',
        }),
    )
    email = forms.EmailField(
        label='Email (используется для входа)',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ivan@example.com',
            'autocomplete': 'email',
        }),
    )
    password1 = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
        }),
        help_text='Минимум 10 символов, заглавная буква, спецсимвол.',
    )
    password2 = forms.CharField(
        label='Пароль (повтор)',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
        }),
    )

    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Пароли не совпадают.')
        return p2

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data.get('password2')
        if password:
            try:
                validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error('password2', error)

    def save(self, commit=True):
        user = super().save(commit=False)

        first = self.cleaned_data.get('first_name', '').strip()
        last  = self.cleaned_data.get('last_name', '').strip()
        user.full_name = f'{last} {first}'.strip()

        user.set_password(self.cleaned_data['password1'])

        user.is_approved   = False
        user.is_staff      = False
        user.role          = User.ROLE_VIEWER
        user.app_access    = ''
        user.requested_app = ''

        if commit:
            user.save()
        return user


class EmailLoginForm(AuthenticationForm):
    """Login form using email instead of username."""

    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ivan@example.com',
            'autofocus': True,
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'current-password',
        }),
    )

    error_messages = {
        'invalid_login': 'Неверный email или пароль.',
        'inactive': 'Аккаунт заблокирован.',
    }

    def clean_username(self):
        return self.cleaned_data['username'].strip().lower()


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('full_name', 'position', 'phone')
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'position':  forms.TextInput(attrs={'class': 'form-control'}),
            'phone':     forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'full_name': 'Полное имя',
            'position':  'Должность',
            'phone':     'Телефон',
        }


class AdminUserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('full_name', 'email', 'department', 'role', 'app_access',
                  'position', 'phone', 'is_approved', 'is_active')
        widgets = {
            'full_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'role':       forms.Select(attrs={'class': 'form-select'}),
            'app_access': forms.Select(attrs={'class': 'form-select'}),
            'position':   forms.TextInput(attrs={'class': 'form-control'}),
            'phone':      forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'full_name':  'Полное имя',
            'email':      'Email',
            'department': 'Отдел',
            'role':       'Роль',
            'app_access': 'Доступ к приложению',
            'position':   'Должность',
            'phone':      'Телефон',
            'is_approved': 'Подтверждён',
            'is_active':   'Активен',
        }
