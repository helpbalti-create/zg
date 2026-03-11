from django import forms
from .models import Project, BudgetSection, BudgetCategory, Expense, BudgetCorrection


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('name', 'description', 'donor', 'project_code', 'start_date', 'end_date', 'total_budget', 'currency')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название проекта'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'donor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CWS, UMCOR...'}),
            'project_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZG-2025-01'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Название проекта',
            'description': 'Описание',
            'donor': 'Донор / Источник финансирования',
            'project_code': 'Код проекта',
            'start_date': 'Дата начала',
            'end_date': 'Дата окончания',
            'total_budget': 'Общий бюджет',
            'currency': 'Валюта',
        }


class BudgetSectionForm(forms.ModelForm):
    class Meta:
        model = BudgetSection
        fields = ('code', 'name', 'order')
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Персонал программы'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'code': 'Код секции',
            'name': 'Название секции',
            'order': 'Порядок',
        }


class BudgetCategoryForm(forms.ModelForm):
    class Meta:
        model = BudgetCategory
        fields = ('section', 'code', 'name', 'unit_measure', 'unit_cost', 'frequency', 'allocated_amount', 'notes', 'order')
        widgets = {
            'section': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PRG11'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Бензин и заправка'}),
            'unit_measure': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Month / Lump sum'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'frequency': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'allocated_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'section': 'Секция',
            'code': 'Код',
            'name': 'Название статьи',
            'unit_measure': 'Единица измерения',
            'unit_cost': 'Стоимость за 1 единицу',
            'frequency': 'Частота / Месяцев',
            'allocated_amount': 'Выделенная сумма',
            'notes': 'Примечания',
            'order': 'Порядок',
        }

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['section'].queryset = BudgetSection.objects.filter(project=project)
        self.fields['section'].empty_label = '— Без секции —'


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ('category', 'quantity', 'amount', 'date', 'period', 'description', 'document_number', 'attachment')
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Заправка машины 22.01.2025'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '№ чека или накладной'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'category': 'Статья расходов',
            'amount': 'Сумма',
            'date': 'Дата',
            'period': 'Отчётный период',
            'description': 'Описание',
            'document_number': 'Номер документа',
            'quantity': 'Количество',
            'attachment': 'Документ (чек, накладная)',
        }

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = BudgetCategory.objects.filter(
            project=project
        ).select_related('section').order_by('section__order', 'order')


class BudgetCorrectionForm(forms.ModelForm):
    class Meta:
        model = BudgetCorrection
        fields = ('category', 'correction_type', 'old_value', 'new_value', 'reason', 'date')
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'correction_type': forms.Select(attrs={'class': 'form-select'}),
            'old_value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Было'}),
            'new_value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Стало'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Причина корректировки'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'category': 'Статья (если применимо)',
            'correction_type': 'Тип корректировки',
            'old_value': 'Старое значение',
            'new_value': 'Новое значение',
            'reason': 'Причина',
            'date': 'Дата',
            'period': 'Отчётный период',
        }

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = BudgetCategory.objects.filter(project=project)
        self.fields['category'].required = False
        self.fields['category'].empty_label = '— Весь проект —'


class ProjectCompleteForm(forms.Form):
    completion_note = forms.CharField(
        label='Итоговое примечание',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=False,
        help_text='Итоги проекта, выводы, комментарии'
    )