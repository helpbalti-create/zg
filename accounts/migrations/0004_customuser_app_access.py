from django.db import migrations, models

APP_CHOICES = [
    ('budget', '💰 Бюджет'),
    ('people', '👥 CRM — Люди'),
    ('all',    '🔑 Все приложения'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_customuser_id_alter_customuser_is_active_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='requested_app',
            field=models.CharField(
                choices=APP_CHOICES,
                default='budget',
                max_length=20,
                verbose_name='Запрошенный доступ',
                help_text='Что пользователь указал при регистрации. Только для справки.',
            ),
        ),
        migrations.AddField(
            model_name='customuser',
            name='app_access',
            field=models.CharField(
                choices=APP_CHOICES,
                default='budget',
                max_length=20,
                verbose_name='Доступ к приложению',
                help_text='Реальный доступ. Задаётся администратором при подтверждении.',
            ),
        ),
    ]
