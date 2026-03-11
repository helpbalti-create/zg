from django.contrib import admin
from django.utils.html import format_html
from core.access import AppAccessAdminMixin
from .models import (
    FieldCategory, FieldDefinition, RelationshipType,
    Family, FamilyMember, Person, PersonFieldValue, PersonRelationship,
)


# ─── Field Definition Admin ────────────────────────────────────────────────────

class FieldCategoryAdmin(AppAccessAdminMixin, admin.ModelAdmin):
    required_app_access = 'people'
    list_display  = ('name', 'order', 'field_count')
    list_editable = ('order',)
    ordering      = ('order',)

    def field_count(self, obj):
        return obj.fields.filter(is_active=True).count()
    field_count.short_description = 'Полей'


class FieldDefinitionAdmin(AppAccessAdminMixin, admin.ModelAdmin):
    required_app_access = 'people'
    list_display  = ('label', 'name', 'field_type', 'category', 'required', 'is_active', 'order')
    list_editable = ('required', 'is_active', 'order')
    list_filter   = ('field_type', 'category', 'required', 'is_active')
    search_fields = ('label', 'name')
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'label', 'field_type', 'help_text'),
        }),
        ('Настройки', {
            'fields': ('choices', 'required', 'is_active', 'order'),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['choices'].widget.attrs['rows'] = 6
        form.base_fields['choices'].widget.attrs['placeholder'] = (
            'Вариант 1\nВариант 2\nВариант 3'
        )
        return form


# ─── Relationship Types Admin ──────────────────────────────────────────────────

class RelationshipTypeAdmin(AppAccessAdminMixin, admin.ModelAdmin):
    required_app_access = 'people'
    list_display  = ('name', 'reverse_name', 'is_family', 'order')
    list_editable = ('is_family', 'order')
    list_filter   = ('is_family',)
    search_fields = ('name', 'reverse_name')


# ─── Family Admin ──────────────────────────────────────────────────────────────

class FamilyMemberInline(admin.TabularInline):
    model       = FamilyMember
    extra       = 1
    fields      = ('person', 'role', 'is_head', 'joined', 'notes')
    autocomplete_fields = ('person',)


class FamilyAdmin(AppAccessAdminMixin, admin.ModelAdmin):
    required_app_access = 'people'
    list_display  = ('name', 'member_count', 'head_name', 'created_at')
    search_fields = ('name', 'address')
    inlines       = (FamilyMemberInline,)
    readonly_fields = ('created_at', 'updated_at')

    def member_count(self, obj):
        count = obj.member_count()
        return format_html('<b>{}</b>', count)
    member_count.short_description = 'Членов'

    def head_name(self, obj):
        head = obj.get_head()
        if head:
            return format_html(
                '<a href="/admin/people/person/{}/change/">{}</a>',
                head.pk, head.full_name,
            )
        return '—'
    head_name.short_description = 'Глава семьи'


# ─── Person Admin ──────────────────────────────────────────────────────────────

class PersonFieldValueInline(admin.StackedInline):
    model   = PersonFieldValue
    extra   = 0
    fields  = ('field', 'value')
    readonly_fields = ()

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('field', 'field__category')


class PersonRelationshipFromInline(admin.TabularInline):
    model                 = PersonRelationship
    fk_name               = 'from_person'
    extra                 = 1
    fields                = ('relationship_type', 'to_person', 'note')
    autocomplete_fields   = ('to_person',)
    verbose_name          = 'Связь (исходящая)'
    verbose_name_plural   = 'Связи (исходящие)'


class FamilyMemberPersonInline(admin.TabularInline):
    model               = FamilyMember
    extra               = 0
    fields              = ('family', 'role', 'is_head')
    autocomplete_fields = ('family',)
    verbose_name        = 'Семья'
    verbose_name_plural = 'Семьи'


class PersonAdmin(AppAccessAdminMixin, admin.ModelAdmin):
    required_app_access = 'people'
    list_display   = ('full_name', 'gender', 'birth_date', 'age_display', 'families_display', 'created_at')
    list_filter    = ('gender',)
    search_fields  = ('full_name',)
    readonly_fields = ('created_at', 'updated_at')
    inlines        = (PersonFieldValueInline, FamilyMemberPersonInline, PersonRelationshipFromInline)

    fieldsets = (
        ('Основные данные', {
            'fields': ('full_name', 'birth_date', 'gender'),
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def age_display(self, obj):
        a = obj.age()
        return f'{a} лет' if a is not None else '—'
    age_display.short_description = 'Возраст'

    def families_display(self, obj):
        families = obj.get_families()
        if not families:
            return '—'
        links = ', '.join(
            f'<a href="/admin/people/family/{f.pk}/change/">{f.name}</a>'
            for f in families
        )
        return format_html(links)
    families_display.short_description = 'Семьи'


class PersonRelationshipAdmin(AppAccessAdminMixin, admin.ModelAdmin):
    required_app_access = 'people'
    list_display  = ('from_person', 'relationship_type', 'to_person', 'note')
    list_filter   = ('relationship_type',)
    search_fields = ('from_person__full_name', 'to_person__full_name')
    autocomplete_fields = ('from_person', 'to_person')


# ─── Register on custom admin_site ────────────────────────────────────────────
from admin_site import admin_site  # noqa: E402

admin_site.register(FieldCategory, FieldCategoryAdmin)
admin_site.register(FieldDefinition, FieldDefinitionAdmin)
admin_site.register(RelationshipType, RelationshipTypeAdmin)
admin_site.register(Family, FamilyAdmin)
admin_site.register(Person, PersonAdmin)
admin_site.register(PersonRelationship, PersonRelationshipAdmin)

# Also register on default admin.site so autodiscover doesn't break
admin.site.register(FieldCategory, FieldCategoryAdmin)
admin.site.register(FieldDefinition, FieldDefinitionAdmin)
admin.site.register(RelationshipType, RelationshipTypeAdmin)
admin.site.register(Family, FamilyAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(PersonRelationship, PersonRelationshipAdmin)
