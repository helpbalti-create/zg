from django.contrib import admin
from core.access import AppAccessAdminMixin
from .models import Project, BudgetSection, BudgetCategory, Expense, BudgetCorrection


class BudgetCategoryInline(admin.TabularInline):
    model = BudgetCategory
    extra = 0


class BudgetSectionInline(admin.TabularInline):
    model = BudgetSection
    extra = 0


class ProjectAdmin(AppAccessAdminMixin, admin.ModelAdmin):
    required_app_access = 'budget'
    list_display = ('name', 'project_code', 'donor', 'total_budget', 'status', 'start_date', 'end_date')
    list_filter  = ('status',)
    inlines      = [BudgetSectionInline]


class BudgetSectionAdmin(AppAccessAdminMixin, admin.ModelAdmin):
    required_app_access = 'budget'
    list_display = ('project', 'code', 'name', 'order')
    inlines      = [BudgetCategoryInline]


class BudgetCategoryAdmin(AppAccessAdminMixin, admin.ModelAdmin):
    required_app_access = 'budget'
    list_display = ('project', 'section', 'code', 'name', 'allocated_amount')
    list_filter  = ('project',)


class ExpenseAdmin(AppAccessAdminMixin, admin.ModelAdmin):
    required_app_access = 'budget'
    list_display = ('date', 'category', 'amount', 'description', 'created_by')
    list_filter  = ('category__project', 'date')
    date_hierarchy = 'date'


class BudgetCorrectionAdmin(AppAccessAdminMixin, admin.ModelAdmin):
    required_app_access = 'budget'
    list_display = ('project', 'category', 'correction_type', 'date', 'created_by')


# ─── Register on custom admin_site ────────────────────────────────────────────
from admin_site import admin_site  # noqa: E402

admin_site.register(Project, ProjectAdmin)
admin_site.register(BudgetSection, BudgetSectionAdmin)
admin_site.register(BudgetCategory, BudgetCategoryAdmin)
admin_site.register(Expense, ExpenseAdmin)
admin_site.register(BudgetCorrection, BudgetCorrectionAdmin)

# Also register on default admin.site so autodiscover doesn't break
admin.site.register(Project, ProjectAdmin)
admin.site.register(BudgetSection, BudgetSectionAdmin)
admin.site.register(BudgetCategory, BudgetCategoryAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(BudgetCorrection, BudgetCorrectionAdmin)
