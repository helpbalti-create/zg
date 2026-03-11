"""
Команда для импорта расходов из статей бюджета.
Логика: для каждой статьи с unit_cost > 0 создаёт расходы по периодам.
  - frequency = 1  → 1 расход (Lump sum)
  - frequency > 1  → N расходов (по одному на каждый период/месяц)
  Сумма каждого расхода = quantity × unit_cost
  Дата  = start_date + (period-1) месяцев

Использование:
  python manage.py import_expenses_from_budget --project_pk=1 [--dry_run]
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from budget.models import Project, BudgetCategory, Expense

User = get_user_model()


class Command(BaseCommand):
    help = 'Импортировать расходы из статей бюджета (по периодам)'

    def add_arguments(self, parser):
        parser.add_argument('--project_pk', type=int, required=True)
        parser.add_argument('--dry_run', action='store_true',
                            help='Только показать что будет создано, не сохранять')
        parser.add_argument('--user_pk', type=int, default=None,
                            help='PK пользователя-автора расходов (по умолч. первый суперюзер)')

    def handle(self, *args, **options):
        project = Project.objects.get(pk=options['project_pk'])
        dry = options['dry_run']
        user_pk = options['user_pk']

        if user_pk:
            user = User.objects.get(pk=user_pk)
        else:
            user = User.objects.filter(is_superuser=True).first()

        self.stdout.write(f'\nПроект: {project.name}')
        self.stdout.write(f'Старт:  {project.start_date}')
        self.stdout.write(f'Автор:  {user}')
        self.stdout.write(f'Режим:  {"DRY RUN" if dry else "РЕАЛЬНАЯ ЗАПИСЬ"}\n')

        total_created = 0
        total_amount = Decimal('0')

        for cat in project.categories.order_by('section__order', 'order'):
            if not cat.unit_cost or cat.unit_cost == 0:
                self.stdout.write(f'  ПРОПУСК (unit_cost=0): {cat.code} {cat.name}')
                continue

            freq = int(cat.frequency) if cat.frequency >= 1 else 1
            amount_per_period = cat.quantity * cat.unit_cost
            description = cat.notes or cat.name
            unit = cat.unit_measure or 'ед.'

            self.stdout.write(
                f'\n  [{cat.code}] {cat.name}\n'
                f'    {cat.quantity} {unit} × ${cat.unit_cost} = ${amount_per_period} × {freq} периодов'
            )

            for period in range(1, freq + 1):
                # Дата: первый день месяца старта + (period-1) месяцев
                date = project.start_date + relativedelta(months=period - 1)

                if not dry:
                    # Не создавать если уже есть расход с таким периодом для этой статьи
                    exists = Expense.objects.filter(
                        category=cat,
                        period=period,
                        description__startswith='[импорт]'
                    ).exists()
                    if exists:
                        self.stdout.write(f'    Период {period}: уже существует — пропуск')
                        continue

                    Expense.objects.create(
                        category=cat,
                        quantity=cat.quantity,
                        amount=amount_per_period,
                        date=date,
                        description=f'[импорт] {description}',
                        period=min(period, 6),
                        created_by=user,
                    )

                self.stdout.write(
                    f'    {"[DRY]" if dry else "[OK]"} Период {period} | {date} | '
                    f'{cat.quantity} {unit} | ${amount_per_period}'
                )
                total_created += 1
                total_amount += amount_per_period

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'Итого расходов: {total_created} | Сумма: ${total_amount:,.2f}')
        if dry:
            self.stdout.write('DRY RUN — ничего не сохранено. Уберите --dry_run для записи.')