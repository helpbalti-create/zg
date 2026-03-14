import importlib
import os
import tempfile
from datetime import date
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Prefetch, DecimalField, Value
from django.db.models.functions import Coalesce
from decimal import Decimal
from collections import OrderedDict
from django.core.exceptions import PermissionDenied
from core.access import require_app_access
from .models import Project, BudgetSection, BudgetCategory, Expense, BudgetCorrection
from .forms import (
    ProjectForm, BudgetSectionForm, BudgetCategoryForm,
    ExpenseForm, BudgetCorrectionForm, ProjectCompleteForm
)
from .export import export_project_to_excel
from .management.commands.import_budget_excel import parse_excel
MONEY_FIELD = DecimalField(max_digits=14, decimal_places=2)
def _category_spent_annotation():
    return Coalesce(Sum('expenses__amount'), Value(Decimal('0.00')), output_field=MONEY_FIELD)
def _project_spent_annotation():
    return Coalesce(Sum('categories__expenses__amount'), Value(Decimal('0.00')), output_field=MONEY_FIELD)
def _section_allocated_annotation():
    return Coalesce(Sum('categories__allocated_amount'), Value(Decimal('0.00')), output_field=MONEY_FIELD)
def _section_spent_annotation():
    return Coalesce(Sum('categories__expenses__amount'), Value(Decimal('0.00')), output_field=MONEY_FIELD)
def ensure_budget_edit_access(user):
    if not user.can_edit_budget():
        raise PermissionDenied('У вас нет прав на изменение данных бюджета.')
def build_code_summary(project):
    """
    Группирует статьи по коду и считает суммарный лимит и расходы.
    Возвращает список словарей, отсортированных по коду.
    """
    summary = {}
    for cat in project.categories.all():
        code = (cat.code or '').strip()
        if not code:
            continue
        if code not in summary:
            summary[code] = {
                'code': code,
                'allocated': Decimal('0'),
                'spent': Decimal('0'),
                'categories': [],
            }
        summary[code]['allocated'] += cat.allocated_amount
        summary[code]['spent'] += cat.total_spent
        summary[code]['categories'].append(cat)
    result = []
    for cs in sorted(summary.values(), key=lambda x: x['code']):
        cs['remaining'] = cs['allocated'] - cs['spent']
        cs['is_over'] = cs['spent'] > cs['allocated']
        cs['pct'] = int(cs['spent'] / cs['allocated'] * 100) if cs['allocated'] else 0
        cs['is_warning'] = cs['pct'] >= 80 and not cs['is_over']
        result.append(cs)
    return result
# Палитра мягких цветов для групп кодов (до 14 разных кодов на секцию)
CODE_COLORS = [
    '#EAF4FB', '#FEF9E7', '#EAFAF1', '#FDEDEC', '#F4ECF7',
    '#E8F8F5', '#FEF5E7', '#EBF5FB', '#F9EBEA', '#E9F7EF',
    '#FDFEFE', '#F0F3FF', '#FFF8E7', '#F5EEF8',
]
def build_section_code_groups(project):
    """
    Для каждой секции возвращает список групп кодов.
    Каждая группа: { code, color, categories, allocated, spent, remaining, pct, is_over, is_warning }
    Статьи без кода идут отдельной группой с code=None.
    """
    result = []
    for section in project.sections.all():
        # Собираем категории по коду, сохраняя порядок первого появления
        code_order = []
        code_cats = OrderedDict()
        for cat in section.categories.all():
            code = (cat.code or '').strip() or None
            if code not in code_cats:
                code_cats[code] = []
                code_order.append(code)
            code_cats[code].append(cat)
        # Назначаем цвет каждому уникальному коду
        color_map = {}
        color_idx = 0
        for code in code_order:
            if code not in color_map:
                color_map[code] = CODE_COLORS[color_idx % len(CODE_COLORS)]
                color_idx += 1
        groups = []
        for code in code_order:
            cats = code_cats[code]
            alloc = sum(c.allocated_amount for c in cats)
            spent = sum(c.total_spent for c in cats)
            rem = alloc - spent
            pct = int(spent / alloc * 100) if alloc else 0
            is_over = spent > alloc
            is_warn = pct >= 80 and not is_over
            groups.append({
                'code': code,
                'color': color_map[code],
                'categories': cats,
                'allocated': alloc,
                'spent': spent,
                'remaining': rem,
                'pct': pct,
                'is_over': is_over,
                'is_warning': is_warn,
                'multi': len(cats) > 1,  # True если несколько строк с этим кодом
            })
        result.append({
            'section': section,
            'groups': groups,
        })
    return result
@require_app_access('budget')
def project_list(request):
    projects = Project.objects.annotate(total_spent=_project_spent_annotation())
    active = projects.filter(status=Project.STATUS_ACTIVE)
    completed = projects.filter(status=Project.STATUS_COMPLETED)
    archived = projects.filter(status=Project.STATUS_ARCHIVED)
    return render(request, 'budget/project_list.html', {
        'active_projects': active,
        'completed_projects': completed,
        'archived_projects': archived,
        'can_edit': request.user.can_edit_budget(),
    })
@require_app_access('budget')
def project_create(request):
    ensure_budget_edit_access(request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            messages.success(request, f'Проект «{project.name}» создан.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, 'budget/project_form.html', {'form': form, 'title': 'Новый проект'})
@require_app_access('budget')
def project_detail(request, pk):
    category_queryset = BudgetCategory.objects.annotate(total_spent=_category_spent_annotation())
    section_queryset = BudgetSection.objects.annotate(
        total_allocated=_section_allocated_annotation(),
        total_spent=_section_spent_annotation(),
    ).prefetch_related(Prefetch('categories', queryset=category_queryset))
    project_queryset = Project.objects.annotate(total_spent=_project_spent_annotation()).prefetch_related(
        Prefetch('sections', queryset=section_queryset),
        Prefetch('categories', queryset=category_queryset),
    )
    project = get_object_or_404(project_queryset, pk=pk)
    sections = project.sections.all()
    categories_no_section = [cat for cat in project.categories.all() if cat.section_id is None]
    recent_expenses = Expense.objects.filter(
        category__project=project
    ).select_related('category', 'created_by').order_by('-date', '-created_at')[:200]
    corrections = project.corrections.select_related('category', 'created_by').all()
    # Сводка по кодам — ключевая фича
    code_summary = build_code_summary(project)
    # Коды с перерасходом — для алертов вверху страницы
    over_codes = [cs for cs in code_summary if cs['is_over']]
    can_edit = request.user.can_edit_budget()
    sections_with_groups = build_section_code_groups(project)
    return render(request, 'budget/project_detail.html', {
        'project': project,
        'sections': sections,
        'sections_with_groups': sections_with_groups,
        'categories_no_section': categories_no_section,
        'recent_expenses': recent_expenses,
        'corrections': corrections,
        'can_edit': can_edit,
        'code_summary': code_summary,
        'over_codes': over_codes,
    })
@require_app_access('budget')
def project_edit(request, pk):
    ensure_budget_edit_access(request.user)
    project = get_object_or_404(Project, pk=pk)
    if project.status == Project.STATUS_COMPLETED:
        messages.error(request, 'Нельзя редактировать завершённый проект.')
        return redirect('project_detail', pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Проект обновлён.')
            return redirect('project_detail', pk=pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'budget/project_form.html', {'form': form, 'title': 'Редактировать проект', 'project': project})
@require_app_access('budget')
def project_complete(request, pk):
    ensure_budget_edit_access(request.user)
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectCompleteForm(request.POST)
        if form.is_valid():
            project.complete(request.user, form.cleaned_data.get('completion_note', ''))
            messages.success(request, f'Проект «{project.name}» завершён.')
            return redirect('project_detail', pk=pk)
    else:
        form = ProjectCompleteForm()
    return render(request, 'budget/project_complete.html', {'form': form, 'project': project})
# --- Sections ---
@require_app_access('budget')
def section_create(request, project_pk):
    ensure_budget_edit_access(request.user)
    project = get_object_or_404(Project, pk=project_pk)
    if request.method == 'POST':
        form = BudgetSectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)
            section.project = project
            section.save()
            messages.success(request, f'Секция «{section.name}» добавлена.')
            return redirect('project_detail', pk=project_pk)
    else:
        form = BudgetSectionForm()
    return render(request, 'budget/section_form.html', {'form': form, 'project': project})
@require_app_access('budget')
def section_edit(request, pk):
    ensure_budget_edit_access(request.user)
    section = get_object_or_404(BudgetSection, pk=pk)
    if request.method == 'POST':
        form = BudgetSectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            return redirect('project_detail', pk=section.project.pk)
    else:
        form = BudgetSectionForm(instance=section)
    return render(request, 'budget/section_form.html', {'form': form, 'project': section.project, 'section': section})
# --- Categories ---
@require_app_access('budget')
def category_create(request, project_pk):
    ensure_budget_edit_access(request.user)
    project = get_object_or_404(Project, pk=project_pk)
    if request.method == 'POST':
        form = BudgetCategoryForm(project, request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.project = project
            cat.save()
            messages.success(request, f'Статья «{cat.name}» добавлена.')
            return redirect('project_detail', pk=project_pk)
    else:
        section_pk = request.GET.get('section')
        initial = {}
        if section_pk:
            initial['section'] = section_pk
        form = BudgetCategoryForm(project, initial=initial)
    return render(request, 'budget/category_form.html', {'form': form, 'project': project})
@require_app_access('budget')
def category_edit(request, pk):
    ensure_budget_edit_access(request.user)
    category = get_object_or_404(BudgetCategory, pk=pk)
    project = category.project
    if request.method == 'POST':
        form = BudgetCategoryForm(project, request.POST, instance=category)
        if form.is_valid():
            old_amount = str(category.allocated_amount)
            form.save()
            new_amount = str(category.allocated_amount)
            if old_amount != new_amount:
                BudgetCorrection.objects.create(
                    project=project,
                    category=category,
                    correction_type='amount',
                    old_value=old_amount,
                    new_value=new_amount,
                    reason='Редактирование статьи',
                    created_by=request.user
                )
            messages.success(request, 'Статья обновлена.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = BudgetCategoryForm(project, instance=category)
    return render(request, 'budget/category_form.html', {'form': form, 'project': project, 'category': category})
@require_app_access('budget')
def category_delete(request, pk):
    ensure_budget_edit_access(request.user)
    category = get_object_or_404(BudgetCategory, pk=pk)
    project_pk = category.project.pk
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Статья удалена.')
    return redirect('project_detail', pk=project_pk)
@require_app_access('budget')
def category_detail(request, pk):
    category = get_object_or_404(BudgetCategory, pk=pk)
    project = category.project
    expenses = category.expenses.select_related('created_by').order_by('period', 'date')
    can_edit = request.user.can_edit_budget()
    return render(request, 'budget/category_detail.html', {
        'category': category,
        'project': project,
        'expenses': expenses,
        'can_edit': can_edit,
    })
# --- Expenses ---
@require_app_access('budget')
def expense_add(request, project_pk):
    ensure_budget_edit_access(request.user)
    project = get_object_or_404(Project, pk=project_pk)
    if project.status == Project.STATUS_COMPLETED:
        messages.error(request, 'Нельзя добавлять расходы в завершённый проект.')
        return redirect('project_detail', pk=project_pk)
    if request.method == 'POST':
        form = ExpenseForm(project, request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            cat = expense.category
            code = (cat.code or '').strip()
            # ── Проверка на уровне КОДА (главная защита от перерасхода) ──────
            if code:
                code_cats = BudgetCategory.objects.filter(project=project, code=code)
                code_allocated = code_cats.aggregate(t=Sum('allocated_amount'))['t'] or Decimal('0')
                code_spent = Expense.objects.filter(
                    category__in=code_cats
                ).aggregate(t=Sum('amount'))['t'] or Decimal('0')
                code_pct = int(code_spent / code_allocated * 100) if code_allocated else 0
                if code_spent > code_allocated:
                    over = code_spent - code_allocated
                    messages.error(
                        request,
                        f'🚨 ПЕРЕРАСХОД ПО КОДУ {code}! '
                        f'Лимит: ${code_allocated:,.2f} | '
                        f'Потрачено: ${code_spent:,.2f} | '
                        f'Превышение: ${over:,.2f}'
                    )
                elif code_pct >= 80:
                    messages.warning(
                        request,
                        f'⚠️ Код {code} использован на {code_pct}% '
                        f'(${code_spent:,.2f} из ${code_allocated:,.2f})'
                    )
                else:
                    messages.success(
                        request,
                        f'✅ Расход ${expense.amount:,.2f} добавлен. '
                        f'Код {code}: использовано {code_pct}% '
                        f'(${code_spent:,.2f} из ${code_allocated:,.2f})'
                    )
            else:
                # Нет кода — проверяем только статью
                if cat.is_over_budget:
                    messages.warning(request, f'⚠️ Статья «{cat.name}» превышает выделенный бюджет!')
                else:
                    messages.success(request, f'Расход ${expense.amount:,.2f} добавлен.')
            return redirect('expense_detail', pk=expense.pk)
    else:
        initial = {}
        cat_pk = request.GET.get('category')
        if cat_pk:
            initial['category'] = cat_pk
        form = ExpenseForm(project, initial=initial)
    return render(request, 'budget/expense_form.html', {'form': form, 'project': project})
@require_app_access('budget')
def expense_edit(request, pk):
    ensure_budget_edit_access(request.user)
    expense = get_object_or_404(Expense, pk=pk)
    project = expense.category.project
    if request.method == 'POST':
        form = ExpenseForm(project, request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Расход обновлён.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ExpenseForm(project, instance=expense)
    return render(request, 'budget/expense_form.html', {'form': form, 'project': project, 'expense': expense})
@require_app_access('budget')
def expense_delete(request, pk):
    ensure_budget_edit_access(request.user)
    expense = get_object_or_404(Expense, pk=pk)
    project_pk = expense.category.project.pk
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Расход удалён.')
    return redirect('project_detail', pk=project_pk)
# --- Corrections ---
@require_app_access('budget')
def correction_add(request, project_pk):
    ensure_budget_edit_access(request.user)
    project = get_object_or_404(Project, pk=project_pk)
    if request.method == 'POST':
        form = BudgetCorrectionForm(project, request.POST)
        if form.is_valid():
            correction = form.save(commit=False)
            correction.project = project
            correction.created_by = request.user
            correction.save()
            if correction.correction_type == 'amount' and correction.category:
                try:
                    new_val = Decimal(correction.new_value)
                    correction.category.allocated_amount = new_val
                    correction.category.save()
                    messages.success(request, f'Корректировка применена. Сумма статьи изменена на {new_val}.')
                except Exception:
                    messages.success(request, 'Корректировка зафиксирована.')
            else:
                messages.success(request, 'Корректировка зафиксирована.')
            return redirect('project_detail', pk=project_pk)
    else:
        form = BudgetCorrectionForm(project)
    return render(request, 'budget/correction_form.html', {'form': form, 'project': project})
@require_app_access('budget')
def expense_detail(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    project = expense.category.project
    can_edit = request.user.can_edit_budget()
    return render(request, 'budget/expense_detail.html', {
        'expense': expense,
        'project': project,
        'can_edit': can_edit,
    })
# --- Export ---
@require_app_access('budget')
def export_excel(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"budget_{project.project_code or project.pk}_{timezone.now().strftime('%Y%m%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    export_project_to_excel(project, response)
    return response
# --- Import expenses from budget ---
@require_app_access('budget')
def import_expenses_preview(request, project_pk):
    """
    GET:  показать предпросмотр что будет импортировано
    POST: выполнить импорт (если confirm=1)
    """
    ensure_budget_edit_access(request.user)
    project = get_object_or_404(Project, pk=project_pk)
    def _build_periods(cat):
        """Возвращает список периодов для статьи."""
        freq = max(1, int(cat.frequency))
        amount_per = cat.quantity * cat.unit_cost
        periods = []
        for i in range(1, freq + 1):
            date = project.start_date + relativedelta(months=i - 1)
            exists = Expense.objects.filter(
                category=cat,
                period=min(i, 6),
                description__startswith='[импорт]',
            ).exists()
            periods.append({
                'num':    i,
                'date':   date.strftime('%d.%m.%Y'),
                'date_obj': date,
                'amount': f'{amount_per:,.2f}',
                'exists': exists,
            })
        return periods
    # POST — выполнить импорт
    if request.method == 'POST' and request.POST.get('confirm') == '1':
        created = 0
        skipped = 0
        total_amount = Decimal('0')
        for cat in project.categories.order_by('section__order', 'order'):
            if not cat.unit_cost or cat.unit_cost == 0:
                continue
            amount_per = cat.quantity * cat.unit_cost
            description = f'[импорт] {cat.notes or cat.name}'
            for p in _build_periods(cat):
                if p['exists']:
                    skipped += 1
                    continue
                Expense.objects.create(
                    category=cat,
                    quantity=cat.quantity,
                    amount=amount_per,
                    date=p['date_obj'],
                    description=description[:500],
                    period=min(p['num'], 6),
                    created_by=request.user,
                )
                created += 1
                total_amount += amount_per
        return render(request, 'budget/import_expenses.html', {
            'project': project,
            'done': True,
            'created_count': created,
            'skipped_count': skipped,
            'total_amount': total_amount,
        })
    # GET — предпросмотр
    preview = []
    to_create = 0
    to_skip = 0
    total_to_create = Decimal('0')
    current_section = None
    section_data = None
    for cat in project.categories.select_related('section').order_by('section__order', 'order'):
        sec_label = (
            f'Секция {cat.section.code}: {cat.section.name}'
            if cat.section else '— Без секции —'
        )
        if sec_label != current_section:
            if section_data:
                preview.append(section_data)
            current_section = sec_label
            section_data = {'section': sec_label, 'rows': []}
        skip = not cat.unit_cost or cat.unit_cost == 0
        amount_per = cat.quantity * cat.unit_cost if not skip else Decimal('0')
        freq = max(1, int(cat.frequency)) if not skip else 0
        periods = _build_periods(cat) if not skip else []
        new_periods = [p for p in periods if not p['exists']]
        to_create += len(new_periods)
        to_skip   += len([p for p in periods if p['exists']])
        total_to_create += amount_per * len(new_periods)
        section_data['rows'].append({
            'code':             cat.code or '—',
            'name':             cat.name,
            'unit':             cat.unit_measure or 'ед.',
            'qty':              cat.quantity,
            'unit_cost':        cat.unit_cost,
            'amount_per_period': f'{amount_per:,.2f}',
            'total_amount':     f'{amount_per * freq:,.2f}',
            'frequency':        freq,
            'notes':            cat.notes,
            'skip':             skip,
            'periods':          periods,
        })
    if section_data:
        preview.append(section_data)
    return render(request, 'budget/import_expenses.html', {
        'project':        project,
        'preview':        preview,
        'to_create':      to_create,
        'to_skip':        to_skip,
        'total_to_create': total_to_create,
        'done':           False,
    })
# --- Full import: Excel → Project + Sections + Categories + Expenses ---
def _ensure_full_import_dependencies():
    for module_name in ('openpyxl',):
        if importlib.util.find_spec(module_name) is None:
            raise ImportError(module_name)
def _save_uploaded_xlsx(xlsx_file):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    for chunk in xlsx_file.chunks():
        tmp.write(chunk)
    tmp.close()
    return tmp.name
def _serialize_import_data(data):
    return {
        'name': data['name'],
        'donor': data['donor'],
        'project_code': data['project_code'],
        'start_date': data['start_date'].isoformat(),
        'end_date': data['end_date'].isoformat(),
        'total_budget': str(data['total_budget']),
        'sections': [
            {
                'code': section['code'],
                'name': section['name'],
                'categories': [
                    {
                        'code': cat['code'],
                        'name': cat['name'],
                        'unit_measure': cat['unit_measure'],
                        'quantity': str(cat['quantity']),
                        'unit_cost': str(cat['unit_cost']),
                        'frequency': str(cat['frequency']),
                        'allocated_amount': str(cat['allocated_amount']),
                        'notes': cat['notes'],
                        'order': cat['order'],
                    }
                    for cat in section['categories']
                ],
            }
            for section in data['sections']
        ],
    }
def _build_full_import_preview(data, existing_action):
    start = data['start_date']
    preview_sections = []
    total_expenses = 0
    total_expenses_amount = Decimal('0')
    total_cats = 0
    existing_warn = ''
    if Project.objects.filter(name=data['name'], start_date=data['start_date']).exists():
        if existing_action == 'error':
            existing_warn = 'Проект с таким именем и датой уже существует — импорт будет остановлен. Смените действие.'
        elif existing_action == 'replace':
            existing_warn = 'Существующий проект и все его данные будут УДАЛЕНЫ и заменены новыми.'
        else:
            existing_warn = 'Проект уже существует — будет сохранён, расходы будут добавлены к нему.'
    for section in data['sections']:
        cats_preview = []
        sec_alloc = Decimal('0')
        for cat in section['categories']:
            freq = max(1, int(cat['frequency']))
            amount_per = cat['quantity'] * cat['unit_cost']
            periods = []
            for period_idx in range(1, freq + 1):
                period_date = start + relativedelta(months=period_idx - 1)
                periods.append({
                    'num': period_idx,
                    'date': period_date.strftime('%d.%m.%Y'),
                    'amount': f'{amount_per:,.2f}',
                })
            total_expenses += freq
            total_expenses_amount += amount_per * freq
            sec_alloc += cat['allocated_amount']
            total_cats += 1
            cats_preview.append({
                'code': cat['code'],
                'name': cat['name'],
                'unit': cat['unit_measure'],
                'qty': cat['quantity'],
                'unit_cost': f"{cat['unit_cost']:,.2f}",
                'amount_per_period': f'{amount_per:,.2f}',
                'total_amount': f'{amount_per * freq:,.2f}',
                'frequency': freq,
                'notes': cat['notes'],
                'periods': periods,
            })
        preview_sections.append({
            'code': section['code'],
            'name': section['name'],
            'cat_count': len(section['categories']),
            'allocated': sec_alloc,
            'categories': cats_preview,
        })
    return {
        'name': data['name'],
        'donor': data['donor'],
        'project_code': data['project_code'],
        'start_date': data['start_date'].strftime('%d.%m.%Y'),
        'end_date': data['end_date'].strftime('%d.%m.%Y'),
        'total_budget': data['total_budget'],
        'sections': preview_sections,
        'total_sections': len(preview_sections),
        'total_cats': total_cats,
        'total_expenses': total_expenses,
        'total_expenses_amount': total_expenses_amount,
        'existing_warning': existing_warn,
        'existing_action': existing_action,
        'cache_key': 'session',
    }
def _get_or_create_import_project(raw, existing_action, user):
    start = date.fromisoformat(raw['start_date'])
    end = date.fromisoformat(raw['end_date'])
    existing_qs = Project.objects.filter(name=raw['name'], start_date=start)
    project = None
    if existing_qs.exists():
        if existing_action == 'error':
            return None, 'Проект уже существует. Вернитесь и смените действие.'
        if existing_action == 'replace':
            existing_qs.delete()
        else:
            project = existing_qs.first()
    if project is None:
        project = Project.objects.create(
            name=raw['name'],
            donor=raw['donor'],
            project_code=raw['project_code'],
            start_date=start,
            end_date=end,
            total_budget=Decimal(raw['total_budget']),
            currency='USD',
            created_by=user,
        )
        for sec_order, section_data in enumerate(raw['sections']):
            section = BudgetSection.objects.create(
                project=project,
                code=section_data['code'],
                name=section_data['name'],
                order=sec_order,
            )
            for cat_data in section_data['categories']:
                BudgetCategory.objects.create(
                    project=project,
                    section=section,
                    code=cat_data['code'],
                    name=cat_data['name'],
                    unit_measure=cat_data['unit_measure'],
                    quantity=Decimal(cat_data['quantity']),
                    unit_cost=Decimal(cat_data['unit_cost']),
                    frequency=Decimal(cat_data['frequency']),
                    allocated_amount=Decimal(cat_data['allocated_amount']),
                    notes=cat_data['notes'],
                    order=cat_data['order'],
                )
    return project, None
def _create_import_expenses(project, start_date, user):
    total_expenses = 0
    total_amount = Decimal('0')
    for cat in project.categories.select_related('section').order_by('section__order', 'order'):
        if not cat.unit_cost or cat.unit_cost == 0:
            continue
        freq = max(1, int(cat.frequency))
        amount_per = cat.quantity * cat.unit_cost
        description = f'[импорт] {cat.notes or cat.name}'[:500]
        for period_idx in range(1, freq + 1):
            period_date = start_date + relativedelta(months=period_idx - 1)
            if Expense.objects.filter(
                category=cat,
                period=min(period_idx, 6),
                description__startswith='[импорт]',
            ).exists():
                continue
            Expense.objects.create(
                category=cat,
                quantity=cat.quantity,
                amount=amount_per,
                date=period_date,
                description=description,
                period=min(period_idx, 6),
                created_by=user,
            )
            total_expenses += 1
            total_amount += amount_per
    return total_expenses, total_amount
def _handle_full_import_preview(request, context):
    xlsx_file = request.FILES.get('xlsx_file')
    if not xlsx_file:
        messages.error(request, 'Выберите файл .xlsx')
        return render(request, 'budget/full_import.html', context)
    temp_path = _save_uploaded_xlsx(xlsx_file)
    try:
        data = parse_excel(temp_path)
    except Exception as exc:
        messages.error(request, f'Ошибка чтения файла: {exc}')
        return render(request, 'budget/full_import.html', context)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    existing_action = request.POST.get('existing_action', 'replace')
    request.session['import_data'] = _serialize_import_data(data)
    request.session['import_existing_action'] = existing_action
    context['preview'] = _build_full_import_preview(data, existing_action)
    return render(request, 'budget/full_import.html', context)
def _handle_full_import_confirm(request, context):
    raw = request.session.get('import_data')
    if not raw:
        messages.error(request, 'Данные сессии истекли. Загрузите файл снова.')
        return render(request, 'budget/full_import.html', context)
    existing_action = request.session.get('import_existing_action', 'replace')
    project, error = _get_or_create_import_project(raw, existing_action, request.user)
    if error:
        messages.error(request, error)
        return render(request, 'budget/full_import.html', context)
    start_date = date.fromisoformat(raw['start_date'])
    total_expenses, total_amount = _create_import_expenses(project, start_date, request.user)
    request.session.pop('import_data', None)
    request.session.pop('import_existing_action', None)
    context['done'] = True
    context['result'] = {
        'project_pk': project.pk,
        'sections': project.sections.count(),
        'categories': project.categories.count(),
        'expenses': total_expenses,
        'total_amount': total_amount,
    }
    return render(request, 'budget/full_import.html', context)
@require_app_access('budget')
def full_import(request):
    ensure_budget_edit_access(request.user)
    try:
        _ensure_full_import_dependencies()
    except ImportError as exc:
        messages.error(request, f'Установите зависимости: {exc}')
        return redirect('project_list')
    context = {'done': False, 'preview': None}
    if request.method == 'POST' and request.POST.get('step') == 'preview':
        return _handle_full_import_preview(request, context)
    if request.method == 'POST' and request.POST.get('step') == 'confirm':
        return _handle_full_import_confirm(request, context)
    return render(request, 'budget/full_import.html', context)
