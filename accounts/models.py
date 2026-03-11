from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone


class Department(models.Model):
    BUDGET = 'budget'
    SOCIAL = 'social'
    EVENTS = 'events'
    VOLUNTEERS = 'volunteers'
    ADMIN_DEPT = 'admin'

    DEPT_CHOICES = [
        (BUDGET, 'Бюджет и финансы'),
        (SOCIAL, 'Социальная помощь'),
        (EVENTS, 'Мероприятия'),
        (VOLUNTEERS, 'Волонтёры'),
        (ADMIN_DEPT, 'Администрация'),
    ]

    name = models.CharField(max_length=50, choices=DEPT_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'

    def __str__(self):
        return self.display_name


class CustomUserManager(BaseUserManager):
    """Manager where EMAIL is the unique identifier (not username)."""

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_approved', True)
        extra_fields.setdefault('role', 'admin')

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_VIEWER = 'viewer'
    ROLE_EDITOR = 'editor'
    ROLE_ADMIN  = 'admin'

    ROLE_CHOICES = [
        (ROLE_VIEWER, 'Только просмотр'),
        (ROLE_EDITOR, 'Просмотр и редактирование'),
        (ROLE_ADMIN,  'Администратор'),
    ]

    # ── App access ─────────────────────────────────────────────────────────────
    APP_BUDGET = 'budget'
    APP_PEOPLE = 'people'
    APP_ALL    = 'all'

    APP_CHOICES = [
        (APP_BUDGET, '💰 Бюджет'),
        (APP_PEOPLE, '👥 CRM — Люди'),
        (APP_ALL,    '🔑 Все приложения'),
    ]

    # ── Core fields ────────────────────────────────────────────────────────────
    email     = models.EmailField('Email', unique=True, db_index=True)
    full_name = models.CharField('Полное имя', max_length=200)

    # ── App access fields ──────────────────────────────────────────────────────
    requested_app = models.CharField(
        'Запрошенный доступ',
        max_length=20,
        choices=APP_CHOICES,
        default=APP_BUDGET,
        help_text='Что пользователь указал при регистрации. Только для справки.',
    )
    app_access = models.CharField(
        'Доступ к приложению',
        max_length=20,
        choices=APP_CHOICES,
        default=APP_BUDGET,
        help_text='Реальный доступ. Задаётся администратором при подтверждении аккаунта.',
    )

    # ── Organisation fields ────────────────────────────────────────────────────
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Отдел',
        related_name='users',
    )
    role = models.CharField(
        'Роль', max_length=20, choices=ROLE_CHOICES, default=ROLE_VIEWER,
    )
    position = models.CharField('Должность', max_length=200, blank=True)
    phone = models.CharField('Телефон', max_length=50, blank=True)

    # ── Account state ──────────────────────────────────────────────────────────
    is_approved = models.BooleanField('Подтверждён', default=False)
    is_staff = models.BooleanField('Персонал', default=False)
    is_active = models.BooleanField('Активен', default=True)
    date_joined = models.DateTimeField('Дата регистрации', default=timezone.now)

    # ── 2FA ────────────────────────────────────────────────────────────────────
    two_factor_enabled = models.BooleanField('2FA включена', default=False)

    # ── Security tracking ─────────────────────────────────────────────────────
    last_login_ip = models.GenericIPAddressField('IP последнего входа', null=True, blank=True)
    password_changed_at = models.DateTimeField('Пароль изменён', null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'           # email is the login field
    REQUIRED_FIELDS = ['full_name']    # asked only by createsuperuser

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.full_name} <{self.email}>'

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else self.email

    # ── App-level access helpers ───────────────────────────────────────────────
    def has_app_access(self, app: str) -> bool:
        """Return True if this user may use the given app slug."""
        if not self.is_active or not self.is_approved:
            return False
        if self.is_superuser:
            return True
        return self.app_access in (app, self.APP_ALL)

    def accessible_apps(self) -> list:
        """Return list of app slugs this user can access."""
        if self.is_superuser or self.app_access == self.APP_ALL:
            return [self.APP_BUDGET, self.APP_PEOPLE]
        return [self.app_access]

    # ── Permission helpers ─────────────────────────────────────────────────────
    def can_edit_budget(self):
        if self.role == self.ROLE_ADMIN or self.is_superuser:
            return True
        return self.role == self.ROLE_EDITOR and bool(
            self.department and self.department.name == Department.BUDGET
        )

    def can_view_budget(self):
        if self.role == self.ROLE_ADMIN or self.is_superuser:
            return True
        return bool(self.department and self.department.name == Department.BUDGET)

    def can_edit_module(self, module_name):
        if self.role == self.ROLE_ADMIN or self.is_superuser:
            return True
        return self.role == self.ROLE_EDITOR and bool(
            self.department and self.department.name == module_name
        )

    def can_view_module(self, module_name):
        if self.role == self.ROLE_ADMIN or self.is_superuser:
            return True
        return bool(self.department and self.department.name == module_name)
