from django import forms
from .models import Person, PersonFieldValue, FieldDefinition, Family, FamilyMember, PersonRelationship


class PersonBaseForm(forms.ModelForm):
    class Meta:
        model  = Person
        fields = ('full_name', 'birth_date', 'gender')
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }


def build_person_form(data=None, instance=None):
    """
    Динамически строит форму для Person + все активные FieldDefinition.
    Возвращает класс формы.
    """
    active_fields = (
        FieldDefinition.objects
        .filter(is_active=True)
        .select_related('category')
        .order_by('category__order', 'order')
    )

    # Существующие значения если редактируем
    existing = {}
    if instance and instance.pk:
        for fv in instance.field_values.select_related('field'):
            existing[fv.field_id] = fv.value

    dynamic_fields = {}
    for fd in active_fields:
        field_kwargs = {
            'label':    fd.label,
            'required': fd.required,
            'help_text': fd.help_text,
            'initial':  existing.get(fd.pk, ''),
        }

        if fd.field_type == FieldDefinition.TEXT:
            dynamic_fields[f'dyn_{fd.name}'] = forms.CharField(**field_kwargs, widget=forms.TextInput())
        elif fd.field_type == FieldDefinition.TEXTAREA:
            dynamic_fields[f'dyn_{fd.name}'] = forms.CharField(**field_kwargs, widget=forms.Textarea(attrs={'rows': 3}))
        elif fd.field_type == FieldDefinition.NUMBER:
            dynamic_fields[f'dyn_{fd.name}'] = forms.DecimalField(**field_kwargs, required=fd.required)
        elif fd.field_type == FieldDefinition.DATE:
            dynamic_fields[f'dyn_{fd.name}'] = forms.DateField(
                **field_kwargs, widget=forms.DateInput(attrs={'type': 'date'})
            )
        elif fd.field_type == FieldDefinition.BOOLEAN:
            dynamic_fields[f'dyn_{fd.name}'] = forms.NullBooleanField(**field_kwargs, widget=forms.Select(
                choices=[('', '—'), ('True', 'Да'), ('False', 'Нет')]
            ))
        elif fd.field_type == FieldDefinition.CHOICE:
            choices = [('', '---------')] + [(c, c) for c in fd.get_choices_list()]
            dynamic_fields[f'dyn_{fd.name}'] = forms.ChoiceField(choices=choices, **field_kwargs)
        elif fd.field_type == FieldDefinition.PHONE:
            dynamic_fields[f'dyn_{fd.name}'] = forms.CharField(**field_kwargs, widget=forms.TextInput(attrs={'type': 'tel'}))
        elif fd.field_type == FieldDefinition.EMAIL:
            dynamic_fields[f'dyn_{fd.name}'] = forms.EmailField(**field_kwargs)

    # Собираем форму динамически
    FormClass = type('DynamicPersonForm', (PersonBaseForm,), dynamic_fields)
    form = FormClass(data=data, instance=instance)
    # Сохраняем определения полей для сохранения значений
    form._dynamic_field_defs = {fd.name: fd for fd in active_fields}
    return form


def save_person_with_dynamic(form, commit=True):
    """Сохраняет Person + все динамические значения полей."""
    person = form.save(commit=commit)
    if commit:
        for name, fd in form._dynamic_field_defs.items():
            value = form.cleaned_data.get(f'dyn_{name}', '')
            if value is None:
                value = ''
            PersonFieldValue.objects.update_or_create(
                person=person, field=fd,
                defaults={'value': str(value)},
            )
    return person


class FamilyForm(forms.ModelForm):
    class Meta:
        model  = Family
        fields = ('name', 'address', 'notes')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
            'notes':   forms.Textarea(attrs={'rows': 2}),
        }


class FamilyMemberForm(forms.ModelForm):
    class Meta:
        model  = FamilyMember
        fields = ('person', 'role', 'is_head', 'joined', 'notes')
        widgets = {
            'joined': forms.DateInput(attrs={'type': 'date'}),
            'notes':  forms.Textarea(attrs={'rows': 2}),
        }


class PersonRelationshipForm(forms.ModelForm):
    class Meta:
        model  = PersonRelationship
        fields = ('to_person', 'relationship_type', 'note')
        widgets = {
            'note': forms.Textarea(attrs={'rows': 2}),
        }
