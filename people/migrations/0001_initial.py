from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FieldSection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100, verbose_name="Название раздела")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
            ],
            options={"ordering": ["order", "name"], "verbose_name": "Раздел полей", "verbose_name_plural": "Разделы полей"},
        ),
        migrations.CreateModel(
            name="FieldDefinition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.SlugField(max_length=80, unique=True, verbose_name="Ключ (латиница, без пробелов)")),
                ("label", models.CharField(max_length=200, verbose_name="Подпись поля")),
                ("field_type", models.CharField(choices=[("text","Строка (текст)"),("textarea","Многострочный текст"),("number","Число"),("date","Дата"),("boolean","Да / Нет"),("choice","Список значений"),("email","Email"),("phone","Телефон"),("file","Файл / документ")], default="text", max_length=20, verbose_name="Тип данных")),
                ("choices_list", models.TextField(blank=True, help_text="Каждый вариант с новой строки", verbose_name="Варианты (для Список значений)")),
                ("is_required", models.BooleanField(default=False, verbose_name="Обязательное")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активно")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("help_text", models.CharField(blank=True, max_length=300, verbose_name="Подсказка")),
                ("section", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="fields", to="people.fieldsection", verbose_name="Раздел")),
            ],
            options={"ordering": ["section__order", "order", "label"], "verbose_name": "Поле анкеты", "verbose_name_plural": "Поля анкеты"},
        ),
        migrations.CreateModel(
            name="FamilyRole",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="Название роли")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
            ],
            options={"ordering": ["order", "name"], "verbose_name": "Роль в семье", "verbose_name_plural": "Роли в семье"},
        ),
        migrations.CreateModel(
            name="RelationshipType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="Название")),
                ("reverse_name", models.CharField(blank=True, help_text="Например: если 'Попечитель' → 'Подопечный'", max_length=100, verbose_name="Обратное название")),
                ("is_bidirectional", models.BooleanField(default=True, help_text="Если да — связь A→B подразумевает B→A", verbose_name="Двусторонняя")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
            ],
            options={"verbose_name": "Тип связи", "verbose_name_plural": "Типы связей"},
        ),
        migrations.CreateModel(
            name="Person",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("first_name", models.CharField(max_length=100, verbose_name="Имя")),
                ("last_name", models.CharField(max_length=100, verbose_name="Фамилия")),
                ("middle_name", models.CharField(blank=True, max_length=100, verbose_name="Отчество")),
                ("birth_date", models.DateField(blank=True, null=True, verbose_name="Дата рождения")),
                ("birth_place", models.CharField(blank=True, max_length=200, verbose_name="Место рождения")),
                ("gender", models.CharField(blank=True, choices=[("M","Мужской"),("F","Женский"),("O","Другой / не указан")], max_length=1, verbose_name="Пол")),
                ("phone", models.CharField(blank=True, max_length=50, verbose_name="Телефон")),
                ("email", models.EmailField(blank=True, verbose_name="Email")),
                ("address", models.TextField(blank=True, verbose_name="Адрес")),
                ("id_number", models.CharField(blank=True, max_length=100, verbose_name="Номер ID / паспорта")),
                ("id_issued_by", models.CharField(blank=True, max_length=200, verbose_name="Выдан кем")),
                ("id_issued_at", models.DateField(blank=True, null=True, verbose_name="Дата выдачи")),
                ("photo", models.ImageField(blank=True, null=True, upload_to="people/photos/", verbose_name="Фото")),
                ("notes", models.TextField(blank=True, verbose_name="Примечания")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Добавлен")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Изменён")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
            ],
            options={"ordering": ["last_name", "first_name"], "verbose_name": "Человек", "verbose_name_plural": "Люди"},
        ),
        migrations.CreateModel(
            name="PersonFieldValue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("value", models.TextField(blank=True, verbose_name="Значение")),
                ("field", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="values", to="people.fielddefinition")),
                ("person", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="field_values", to="people.person")),
            ],
            options={"verbose_name": "Значение поля", "verbose_name_plural": "Значения полей", "unique_together": {("person", "field")}},
        ),
        migrations.CreateModel(
            name="PersonDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=200, verbose_name="Название документа")),
                ("file", models.FileField(upload_to="people/docs/", verbose_name="Файл")),
                ("uploaded_at", models.DateTimeField(auto_now_add=True, verbose_name="Загружен")),
                ("notes", models.TextField(blank=True, verbose_name="Примечания")),
                ("person", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documents", to="people.person")),
            ],
            options={"verbose_name": "Документ", "verbose_name_plural": "Документы"},
        ),
        migrations.CreateModel(
            name="Family",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(blank=True, help_text="Необязательно — если пусто, генерируется автоматически по фамилии", max_length=200, verbose_name="Название семьи")),
                ("address", models.TextField(blank=True, verbose_name="Адрес семьи")),
                ("notes", models.TextField(blank=True, verbose_name="Примечания")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
            ],
            options={"verbose_name": "Семья", "verbose_name_plural": "Семьи"},
        ),
        migrations.CreateModel(
            name="FamilyMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("is_head", models.BooleanField(default=False, verbose_name="Глава семьи")),
                ("joined_at", models.DateField(blank=True, null=True, verbose_name="Вступил(а)")),
                ("notes", models.TextField(blank=True, verbose_name="Примечания")),
                ("family", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="people.family")),
                ("person", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="people.person")),
                ("role", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="people.familyrole", verbose_name="Роль")),
            ],
            options={"verbose_name": "Член семьи", "verbose_name_plural": "Члены семьи", "unique_together": {("family", "person")}},
        ),
        migrations.AddField(
            model_name="family",
            name="members",
            field=models.ManyToManyField(related_name="families", through="people.FamilyMembership", to="people.person", verbose_name="Члены семьи"),
        ),
        migrations.CreateModel(
            name="PersonRelationship",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("notes", models.TextField(blank=True, verbose_name="Примечания")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("from_person", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="relationships_from", to="people.person", verbose_name="От")),
                ("to_person", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="relationships_to", to="people.person", verbose_name="К")),
                ("relationship_type", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="people.relationshiptype", verbose_name="Тип связи")),
            ],
            options={"verbose_name": "Связь", "verbose_name_plural": "Связи между людьми", "unique_together": {("from_person", "to_person", "relationship_type")}},
        ),
    ]
