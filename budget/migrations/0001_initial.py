from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300, verbose_name='Название проекта')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('donor', models.CharField(blank=True, max_length=200, verbose_name='Донор / Источник финансирования')),
                ('project_code', models.CharField(blank=True, max_length=50, verbose_name='Код проекта')),
                ('start_date', models.DateField(verbose_name='Дата начала')),
                ('end_date', models.DateField(verbose_name='Дата окончания')),
                ('total_budget', models.DecimalField(decimal_places=2, max_digits=14, verbose_name='Общий бюджет (USD)')),
                ('currency', models.CharField(default='USD', max_length=10, verbose_name='Валюта')),
                ('status', models.CharField(
                    choices=[
                        ('active', 'Активный'),
                        ('completed', 'Завершён'),
                        ('archived', 'Архив'),
                    ],
                    default='active',
                    max_length=20,
                    verbose_name='Статус'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата завершения')),
                ('completion_note', models.TextField(blank=True, verbose_name='Примечание при завершении')),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_projects',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Проект',
                'verbose_name_plural': 'Проекты',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BudgetSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10, verbose_name='Код секции')),
                ('name', models.CharField(max_length=200, verbose_name='Название секции')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sections',
                    to='budget.project'
                )),
            ],
            options={
                'verbose_name': 'Секция бюджета',
                'verbose_name_plural': 'Секции бюджета',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='BudgetCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=20, verbose_name='Код статьи')),
                ('name', models.CharField(max_length=300, verbose_name='Название статьи')),
                ('unit_measure', models.CharField(blank=True, default='Lump sum', max_length=50, verbose_name='Единица измерения')),
                ('quantity', models.DecimalField(decimal_places=2, default=1, max_digits=10, verbose_name='Количество')),
                ('unit_cost', models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='Стоимость единицы')),
                ('frequency', models.DecimalField(decimal_places=2, default=1, max_digits=10, verbose_name='Частота / Кол-во месяцев')),
                ('allocated_amount', models.DecimalField(decimal_places=2, max_digits=14, verbose_name='Выделено (итого)')),
                ('notes', models.TextField(blank=True, verbose_name='Примечания')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='categories',
                    to='budget.project'
                )),
                ('section', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='categories',
                    to='budget.budgetsection'
                )),
            ],
            options={
                'verbose_name': 'Статья бюджета',
                'verbose_name_plural': 'Статьи бюджета',
                'ordering': ['section__order', 'order'],
            },
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14, verbose_name='Сумма')),
                ('date', models.DateField(default=django.utils.timezone.now, verbose_name='Дата расхода')),
                ('description', models.CharField(max_length=500, verbose_name='Описание / Назначение')),
                ('document_number', models.CharField(blank=True, max_length=100, verbose_name='Номер документа / чека')),
                ('attachment', models.FileField(blank=True, null=True, upload_to='expenses/', verbose_name='Документ')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='expenses',
                    to='budget.budgetcategory'
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='expenses',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Расход',
                'verbose_name_plural': 'Расходы',
                'ordering': ['-date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BudgetCorrection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('correction_type', models.CharField(
                    choices=[
                        ('amount', 'Изменение суммы'),
                        ('name', 'Изменение названия'),
                        ('add_category', 'Добавление статьи'),
                        ('remove_category', 'Удаление статьи'),
                        ('other', 'Другое'),
                    ],
                    default='amount',
                    max_length=50,
                    verbose_name='Тип корректировки'
                )),
                ('old_value', models.TextField(blank=True, verbose_name='Старое значение')),
                ('new_value', models.TextField(blank=True, verbose_name='Новое значение')),
                ('reason', models.TextField(verbose_name='Причина корректировки')),
                ('date', models.DateField(default=django.utils.timezone.now, verbose_name='Дата корректировки')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='corrections',
                    to='budget.budgetcategory'
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='corrections',
                    to=settings.AUTH_USER_MODEL
                )),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='corrections',
                    to='budget.project'
                )),
            ],
            options={
                'verbose_name': 'Корректировка бюджета',
                'verbose_name_plural': 'Корректировки бюджета',
                'ordering': ['-created_at'],
            },
        ),
    ]
