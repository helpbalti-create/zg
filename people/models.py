from django.db import models
from django.core.exceptions import ValidationError


# ─── Dynamic Field Definitions ────────────────────────────────────────────────

class FieldCategory(models.Model):
    """Группа полей — например 'Личные данные', 'Документы', 'Здоровье'."""
    name  = models.CharField('Название категории', max_length=100)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Категория полей'
        verbose_name_plural = 'Категории полей'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class FieldDefinition(models.Model):
    TEXT     = 'text'
    NUMBER   = 'number'
    DATE     = 'date'
    BOOLEAN  = 'boolean'
    CHOICE   = 'choice'
    TEXTAREA = 'textarea'
    PHONE    = 'phone'
    EMAIL    = 'email'

    FIELD_TYPES = [
        (TEXT,     'Текст (строка)'),
        (NUMBER,   'Число'),
        (DATE,     'Дата'),
        (BOOLEAN,  'Да / Нет'),
        (CHOICE,   'Выбор из списка'),
        (TEXTAREA, 'Длинный текст'),
        (PHONE,    'Телефон'),
        (EMAIL,    'Email'),
    ]

    category   = models.ForeignKey(
        FieldCategory, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Категория', related_name='fields',
    )
    name       = models.SlugField('Системное имя', max_length=100, unique=True,
                                  help_text='Латинские буквы и подчёркивания. Пример: passport_number')
    label      = models.CharField('Название поля', max_length=200)
    field_type = models.CharField('Тип поля', max_length=20, choices=FIELD_TYPES, default=TEXT)
    choices    = models.TextField('Варианты выбора', blank=True,
                                  help_text='Каждый вариант на новой строке. Только для «Выбор из списка».')
    required   = models.BooleanField('Обязательное', default=False)
    order      = models.PositiveIntegerField('Порядок', default=0)
    is_active  = models.BooleanField('Активно', default=True)
    help_text  = models.CharField('Подсказка', max_length=500, blank=True)

    class Meta:
        verbose_name = 'Поле анкеты'
        verbose_name_plural = 'Поля анкеты'
        ordering = ['category__order', 'order', 'label']

    def __str__(self):
        return f'{self.label} [{self.get_field_type_display()}]'

    def get_choices_list(self):
        return [c.strip() for c in self.choices.splitlines() if c.strip()]


# ─── Relationship Types ────────────────────────────────────────────────────────

class RelationshipType(models.Model):
    name         = models.CharField('Название', max_length=100)
    reverse_name = models.CharField('Обратное название', max_length=100, blank=True,
                                    help_text='Пример: "Отец" ↔ "Сын/Дочь"')
    is_family    = models.BooleanField('Семейная связь', default=True,
                                       help_text='Снимите для внесемейных (сосед, попечитель...)')
    order        = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Тип связи'
        verbose_name_plural = 'Типы связей'
        ordering = ['order', 'name']

    def __str__(self):
        if self.reverse_name:
            return f'{self.name} ↔ {self.reverse_name}'
        return self.name


# ─── Family ────────────────────────────────────────────────────────────────────

class Family(models.Model):
    name       = models.CharField('Название / номер дела', max_length=200)
    address    = models.TextField('Адрес проживания', blank=True)
    notes      = models.TextField('Примечания', blank=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'Семья'
        verbose_name_plural = 'Семьи'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_head(self):
        m = self.members.filter(is_head=True).select_related('person').first()
        return m.person if m else None

    def member_count(self):
        return self.members.count()


# ─── Person ────────────────────────────────────────────────────────────────────

class Person(models.Model):
    MALE   = 'M'
    FEMALE = 'F'
    OTHER  = 'O'
    GENDER_CHOICES = [
        (MALE,   'Мужской'),
        (FEMALE, 'Женский'),
        (OTHER,  'Другой / не указан'),
    ]

    full_name  = models.CharField('Полное имя', max_length=200, db_index=True)
    birth_date = models.DateField('Дата рождения', null=True, blank=True)
    gender     = models.CharField('Пол', max_length=1, choices=GENDER_CHOICES, blank=True, default='')
    created_at = models.DateTimeField('Добавлен', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Человек'
        verbose_name_plural = 'Люди'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

    def age(self):
        from datetime import date
        if not self.birth_date:
            return None
        return (date.today() - self.birth_date).days // 365

    def get_field_value(self, field_name):
        try:
            return self.field_values.get(field__name=field_name).value
        except PersonFieldValue.DoesNotExist:
            return ''

    def get_families(self):
        return Family.objects.filter(members__person=self).distinct()


# ─── Dynamic Field Values ──────────────────────────────────────────────────────

class PersonFieldValue(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE,
                               related_name='field_values', verbose_name='Человек')
    field  = models.ForeignKey(FieldDefinition, on_delete=models.CASCADE, verbose_name='Поле')
    value  = models.TextField('Значение', blank=True)

    class Meta:
        verbose_name = 'Значение поля'
        verbose_name_plural = 'Значения полей'
        unique_together = ('person', 'field')

    def __str__(self):
        return f'{self.person} / {self.field.label}: {self.value}'


# ─── Family Membership ─────────────────────────────────────────────────────────

class FamilyMember(models.Model):
    family  = models.ForeignKey(Family, on_delete=models.CASCADE,
                                related_name='members', verbose_name='Семья')
    person  = models.ForeignKey(Person, on_delete=models.CASCADE,
                                related_name='family_memberships', verbose_name='Человек')
    role    = models.ForeignKey(RelationshipType, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='Роль в семье',
                                limit_choices_to={'is_family': True})
    is_head = models.BooleanField('Глава семьи', default=False)
    joined  = models.DateField('Дата вступления', null=True, blank=True)
    notes   = models.TextField('Примечания', blank=True)

    class Meta:
        verbose_name = 'Член семьи'
        verbose_name_plural = 'Члены семьи'
        unique_together = ('family', 'person')

    def __str__(self):
        role_str = self.role.name if self.role else 'без роли'
        return f'{self.person} → {self.family} ({role_str})'

    def clean(self):
        if self.is_head:
            qs = FamilyMember.objects.filter(family=self.family, is_head=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError('В семье может быть только один глава.')


# ─── Person ↔ Person Relationships ────────────────────────────────────────────

class PersonRelationship(models.Model):
    from_person       = models.ForeignKey(Person, on_delete=models.CASCADE,
                                          related_name='relationships_from', verbose_name='От')
    to_person         = models.ForeignKey(Person, on_delete=models.CASCADE,
                                          related_name='relationships_to', verbose_name='Кому')
    relationship_type = models.ForeignKey(RelationshipType, on_delete=models.CASCADE,
                                          verbose_name='Тип связи')
    note              = models.TextField('Примечание', blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Связь'
        verbose_name_plural = 'Связи'
        unique_together = ('from_person', 'to_person', 'relationship_type')

    def __str__(self):
        return f'{self.from_person} —[{self.relationship_type.name}]→ {self.to_person}'

    def clean(self):
        if self.from_person_id and self.from_person_id == self.to_person_id:
            raise ValidationError('Человек не может быть связан сам с собой.')
