from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import CustomUser, Department
from admin_site import admin_site


# ─── Actions ──────────────────────────────────────────────────────────────────

def approve_budget(modeladmin, request, queryset):
    queryset.update(is_approved=True, app_access='budget')
    messages.success(request, f'✅ Одобрено {queryset.count()} пользователей → 💰 Бюджет')
approve_budget.short_description = '✅ Одобрить → 💰 Бюджет'

def approve_people(modeladmin, request, queryset):
    queryset.update(is_approved=True, app_access='people')
    messages.success(request, f'✅ Одобрено {queryset.count()} пользователей → 👥 CRM')
approve_people.short_description = '✅ Одобрить → 👥 CRM'

def approve_all_apps(modeladmin, request, queryset):
    queryset.update(is_approved=True, app_access='all')
    messages.success(request, f'✅ Одобрено {queryset.count()} пользователей → 🔑 Все приложения')
approve_all_apps.short_description = '✅ Одобрить → 🔑 Все приложения'

def revoke_access(modeladmin, request, queryset):
    queryset.update(is_approved=False)
    messages.warning(request, f'⛔ Доступ отозван у {queryset.count()} пользователей')
revoke_access.short_description = '⛔ Отозвать доступ'

def set_access_budget(modeladmin, request, queryset):
    queryset.update(app_access='budget')
    messages.success(request, f'🔄 Доступ изменён → 💰 Бюджет')
set_access_budget.short_description = '🔄 Сменить доступ → 💰 Бюджет'

def set_access_people(modeladmin, request, queryset):
    queryset.update(app_access='people')
    messages.success(request, f'🔄 Доступ изменён → 👥 CRM')
set_access_people.short_description = '🔄 Сменить доступ → 👥 CRM'

def set_access_all(modeladmin, request, queryset):
    queryset.update(app_access='all')
    messages.success(request, f'🔄 Доступ изменён → 🔑 Все приложения')
set_access_all.short_description = '🔄 Сменить доступ → 🔑 Все'


# ─── ModelAdmins ──────────────────────────────────────────────────────────────

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name')


class CustomUserAdmin(BaseUserAdmin):
    list_display  = (
        'email', 'full_name', 'requested_app_badge',
        'app_access_badge', 'role', 'is_approved', 'is_active', 'two_factor_enabled',
    )
    list_filter   = ('app_access', 'role', 'is_approved', 'is_active', 'two_factor_enabled')
    list_editable = ('is_approved',)
    search_fields = ('email', 'full_name')
    ordering      = ('is_approved', 'email')
    actions       = [
        approve_budget, approve_people, approve_all_apps,
        set_access_budget, set_access_people, set_access_all,
        revoke_access,
    ]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личные данные', {'fields': ('full_name', 'position', 'phone')}),
        ('Организация', {'fields': ('department', 'role')}),
        ('🔐 Доступ к приложениям', {
            'fields': ('requested_app', 'app_access'),
            'description': (
                'requested_app — что пользователь выбрал при регистрации (только для справки). '
                'app_access — реальный доступ, задайте при подтверждении аккаунта.'
            ),
        }),
        ('Статус аккаунта', {
            'fields': ('is_approved', 'is_active', 'is_staff', 'is_superuser', 'two_factor_enabled'),
        }),
        ('Безопасность', {
            'fields': ('last_login_ip', 'password_changed_at', 'last_login', 'date_joined'),
        }),
        ('Группы', {'fields': ('groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'full_name', 'app_access', 'department', 'role',
                'password1', 'password2', 'is_approved',
            ),
        }),
    )
    readonly_fields = (
        'requested_app', 'last_login_ip', 'password_changed_at',
        'last_login', 'date_joined',
    )

    def requested_app_badge(self, obj):
        colors = {'budget': '#1a56db', 'people': '#057a55', 'all': '#6b21a8'}
        labels = {'budget': '💰 Бюджет', 'people': '👥 CRM', 'all': '🔑 Все'}
        color = colors.get(obj.requested_app, '#555')
        label = labels.get(obj.requested_app, obj.requested_app)
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px">{}</span>',
            color, label,
        )
    requested_app_badge.short_description = 'Запросил'

    def app_access_badge(self, obj):
        colors = {'budget': '#1a56db', 'people': '#057a55', 'all': '#6b21a8'}
        labels = {'budget': '💰 Бюджет', 'people': '👥 CRM', 'all': '🔑 Все'}
        color = colors.get(obj.app_access, '#555')
        label = labels.get(obj.app_access, obj.app_access)
        icon = '✅' if obj.is_approved else '⏳'
        return format_html(
            '{} <span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px">{}</span>',
            icon, color, label,
        )
    app_access_badge.short_description = 'Доступ'


# ─── Register on both admin sites ─────────────────────────────────────────────

admin.site.register(Department, DepartmentAdmin)
admin.site.register(CustomUser, CustomUserAdmin)

admin_site.register(Department, DepartmentAdmin)
admin_site.register(CustomUser, CustomUserAdmin)
