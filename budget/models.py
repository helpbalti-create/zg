from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class Project(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_ARCHIVED = 'archived'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Активный'),
        (STATUS_COMPLETED, 'Завершён'),
        (STATUS_ARCHIVED, 'Архив'),
    ]

    name = models.CharField('Название проекта', max_length=300)
    description = models.TextField('Описание', blank=True)
    donor = models.CharField('Донор / Источник финансирования', max_length=200, blank=True)
    project_code = models.CharField('Код проекта', max_length=50, blank=True)
    start_date = models.DateField('Дата начала')
    end_date = models.DateField('Дата окончания')
    total_budget = models.DecimalField('Общий бюджет (USD)', max_digits=14, decimal_places=2)
    currency = models.CharField('Валюта', max_length=10, default='USD')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField('Дата завершения', null=True, blank=True)
    completion_note = models.TextField('Примечание при завершении', blank=True)

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def duration_months(self):
        delta = (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month)
        return max(1, delta)

    @property
    def total_allocated(self):
        return self.categories.aggregate(
            total=models.Sum('allocated_amount')
        )['total'] or Decimal('0')

    @property
    def total_spent(self):
        return Expense.objects.filter(
            category__project=self
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

    @property
    def total_remaining(self):
        return self.total_budget - self.total_spent

    @property
    def spent_percent(self):
        if self.total_budget == 0:
            return 0
        return int((self.total_spent / self.total_budget) * 100)

    def complete(self, user, note=''):
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.completion_note = note
        self.save()


class BudgetSection(models.Model):
    """Секция бюджета (A, B, C, D и т.д.) — как в шаблоне Excel"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sections')
    code = models.CharField('Код секции', max_length=10)
    name = models.CharField('Название секции', max_length=200)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Секция бюджета'
        verbose_name_plural = 'Секции бюджета'
        ordering = ['order']

    def __str__(self):
        return f'{self.code}: {self.name}'

    @property
    def total_allocated(self):
        return self.categories.aggregate(
            total=models.Sum('allocated_amount')
        )['total'] or Decimal('0')

    @property
    def total_spent(self):
        return Expense.objects.filter(
            category__section=self
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')


class BudgetCategory(models.Model):
    """Статья бюджета — конкретная строка расходов"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='categories')
    section = models.ForeignKey(BudgetSection, on_delete=models.SET_NULL, null=True, blank=True, related_name='categories')
    code = models.CharField('Код статьи', max_length=20, blank=True)
    name = models.CharField('Название статьи', max_length=300)
    unit_measure = models.CharField('Единица измерения', max_length=50, blank=True, default='Lump sum')
    quantity = models.DecimalField('Количество', max_digits=10, decimal_places=2, default=1)
    unit_cost = models.DecimalField('Стоимость единицы', max_digits=14, decimal_places=2, default=0)
    frequency = models.DecimalField('Частота / Кол-во месяцев', max_digits=10, decimal_places=2, default=1)
    allocated_amount = models.DecimalField('Выделено (итого)', max_digits=14, decimal_places=2)
    notes = models.TextField('Примечания', blank=True)
    order = models.PositiveIntegerField('Порядок', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Статья бюджета'
        verbose_name_plural = 'Статьи бюджета'
        ordering = ['section__order', 'order']

    def __str__(self):
        return f'{self.code} — {self.name}'

    @property
    def planned_total_qty(self):
        """Плановое кол-во единиц за весь период: quantity × frequency"""
        return self.quantity * self.frequency

    @property
    def total_quantity_spent(self):
        return self.expenses.aggregate(
            total=models.Sum('quantity')
        )['total'] or Decimal('0')

    @property
    def total_spent(self):
        return self.expenses.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')

    @property
    def remaining(self):
        return self.allocated_amount - self.total_spent

    @property
    def spent_percent(self):
        if self.allocated_amount == 0:
            return 0
        return int((self.total_spent / self.allocated_amount) * 100)

    @property
    def is_over_budget(self):
        return self.total_spent > self.allocated_amount

    @property
    def is_warning(self):
        return self.spent_percent >= 80 and not self.is_over_budget

    def save(self, *args, **kwargs):
        if not self.allocated_amount:
            self.allocated_amount = self.quantity * self.unit_cost * self.frequency
        super().save(*args, **kwargs)


class Expense(models.Model):
    """Фактический расход по статье"""
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE, related_name='expenses')
    quantity = models.DecimalField('Количество', max_digits=10, decimal_places=2, default=1)
    amount = models.DecimalField('Сумма', max_digits=14, decimal_places=2)
    date = models.DateField('Дата расхода', default=timezone.now)
    description = models.CharField('Описание / Назначение', max_length=500)
    document_number = models.CharField('Номер документа / чека', max_length=100, blank=True)
    attachment = models.FileField('Документ', upload_to='expenses/', blank=True, null=True)
    period = models.PositiveSmallIntegerField(
        'Отчётный период',
        default=1,
        choices=[(i, f'Период {i}') for i in range(1, 7)],
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Расход'
        verbose_name_plural = 'Расходы'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'{self.date} | {self.category.name} | {self.amount}'


class BudgetCorrection(models.Model):
    """История корректировок бюджета"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='corrections')
    category = models.ForeignKey(BudgetCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='corrections')
    correction_type = models.CharField('Тип корректировки', max_length=50, choices=[
        ('amount', 'Изменение суммы'),
        ('name', 'Изменение названия'),
        ('add_category', 'Добавление статьи'),
        ('remove_category', 'Удаление статьи'),
        ('other', 'Другое'),
    ], default='amount')
    old_value = models.TextField('Старое значение', blank=True)
    new_value = models.TextField('Новое значение', blank=True)
    reason = models.TextField('Причина корректировки')
    date = models.DateField('Дата корректировки', default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='corrections')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Корректировка бюджета'
        verbose_name_plural = 'Корректировки бюджета'
        ordering = ['-created_at']

    def __str__(self):
        return f'Корректировка {self.project.name} — {self.date}'