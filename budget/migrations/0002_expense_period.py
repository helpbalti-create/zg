from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('budget', '0001_initial')]
    operations = [
        migrations.AddField(
            model_name='expense',
            name='period',
            field=models.PositiveSmallIntegerField(
                verbose_name='Отчётный период', default=1,
                choices=[(i, f'Период {i}') for i in range(1, 7)],
            ),
        ),
    ]
