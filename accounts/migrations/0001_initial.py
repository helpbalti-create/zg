from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(
                    choices=[
                        ('budget', 'Бюджет и финансы'),
                        ('social', 'Социальная помощь'),
                        ('events', 'Мероприятия'),
                        ('volunteers', 'Волонтёры'),
                        ('admin', 'Администрация'),
                    ],
                    max_length=50, unique=True, verbose_name='Название'
                )),
                ('display_name', models.CharField(max_length=100, verbose_name='Отображаемое название')),
            ],
            options={'verbose_name': 'Отдел', 'verbose_name_plural': 'Отделы'},
        ),
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, verbose_name='superuser status')),
                ('email', models.EmailField(db_index=True, unique=True, verbose_name='Email')),
                ('full_name', models.CharField(max_length=200, verbose_name='Полное имя')),
                ('role', models.CharField(
                    choices=[
                        ('viewer', 'Только просмотр'),
                        ('editor', 'Просмотр и редактирование'),
                        ('admin', 'Администратор'),
                    ],
                    default='viewer', max_length=20, verbose_name='Роль'
                )),
                ('position', models.CharField(blank=True, max_length=200, verbose_name='Должность')),
                ('phone', models.CharField(blank=True, max_length=50, verbose_name='Телефон')),
                ('is_approved', models.BooleanField(default=False, verbose_name='Подтверждён')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Персонал')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата регистрации')),
                ('two_factor_enabled', models.BooleanField(default=False, verbose_name='2FA включена')),
                ('last_login_ip', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP последнего входа')),
                ('password_changed_at', models.DateTimeField(blank=True, null=True, verbose_name='Пароль изменён')),
                ('department', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='users',
                    to='accounts.department',
                    verbose_name='Отдел',
                )),
                ('groups', models.ManyToManyField(
                    blank=True, related_name='user_set', related_query_name='user',
                    to='auth.group', verbose_name='groups',
                )),
                ('user_permissions', models.ManyToManyField(
                    blank=True, related_name='user_set', related_query_name='user',
                    to='auth.permission', verbose_name='user permissions',
                )),
            ],
            options={'verbose_name': 'Пользователь', 'verbose_name_plural': 'Пользователи'},
        ),
    ]
