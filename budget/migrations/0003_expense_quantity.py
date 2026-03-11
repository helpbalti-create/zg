from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0002_expense_period'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='quantity',
            field=models.DecimalField(
                verbose_name='Количество',
                max_digits=10,
                decimal_places=2,
                default=1,
            ),
        ),
    ]