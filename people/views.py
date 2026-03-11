from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.forms import inlineformset_factory

from core.access import require_app_access

from .models import (
    Person, Family, FamilyMember, PersonRelationship,
    FieldDefinition, RelationshipType,
)
from .forms import (
    build_person_form, save_person_with_dynamic,
    FamilyForm, FamilyMemberForm, PersonRelationshipForm,
)


# ─── Dashboard ─────────────────────────────────────────────────────────────────

@require_app_access('people')
def dashboard(request):
    ctx = {
        'total_people':   Person.objects.count(),
        'total_families': Family.objects.count(),
        'recent_people':  Person.objects.order_by('-created_at')[:5],
        'recent_families': Family.objects.order_by('-created_at')[:5],
    }
    return render(request, 'people/dashboard.html', ctx)


# ─── People ────────────────────────────────────────────────────────────────────

@require_app_access('people')
def person_list(request):
    q = request.GET.get('q', '').strip()
    people = Person.objects.prefetch_related('family_memberships__family')
    if q:
        people = people.filter(full_name__icontains=q)
    return render(request, 'people/person_list.html', {'people': people, 'q': q})


@require_app_access('people')
def person_detail(request, pk):
    person = get_object_or_404(Person, pk=pk)
    # Группируем значения динамических полей по категории
    field_values = (
        person.field_values
        .select_related('field', 'field__category')
        .order_by('field__category__order', 'field__order')
    )
    grouped = {}
    for fv in field_values:
        cat = fv.field.category.name if fv.field.category else 'Прочее'
        grouped.setdefault(cat, []).append(fv)

    families   = FamilyMember.objects.filter(person=person).select_related('family', 'role')
    outgoing   = person.relationships_from.select_related('to_person', 'relationship_type')
    incoming   = person.relationships_to.select_related('from_person', 'relationship_type')

    ctx = {
        'person':   person,
        'grouped':  grouped,
        'families': families,
        'outgoing': outgoing,
        'incoming': incoming,
    }
    return render(request, 'people/person_detail.html', ctx)


@require_app_access('people')
def person_create(request):
    if request.method == 'POST':
        form = build_person_form(data=request.POST)
        if form.is_valid():
            person = save_person_with_dynamic(form)
            messages.success(request, f'✅ Человек «{person.full_name}» добавлен.')
            return redirect('people:person_detail', pk=person.pk)
    else:
        form = build_person_form()

    field_defs = FieldDefinition.objects.filter(is_active=True).select_related('category').order_by('category__order', 'order')
    return render(request, 'people/person_form.html', {
        'form': form, 'field_defs': field_defs, 'action': 'Добавить человека'
    })


@require_app_access('people')
def person_edit(request, pk):
    person = get_object_or_404(Person, pk=pk)
    if request.method == 'POST':
        form = build_person_form(data=request.POST, instance=person)
        if form.is_valid():
            save_person_with_dynamic(form)
            messages.success(request, f'✅ Данные обновлены.')
            return redirect('people:person_detail', pk=person.pk)
    else:
        form = build_person_form(instance=person)

    field_defs = FieldDefinition.objects.filter(is_active=True).select_related('category').order_by('category__order', 'order')
    return render(request, 'people/person_form.html', {
        'form': form, 'field_defs': field_defs, 'action': 'Редактировать', 'person': person
    })


@require_app_access('people')
def person_delete(request, pk):
    person = get_object_or_404(Person, pk=pk)
    if request.method == 'POST':
        name = person.full_name
        person.delete()
        messages.success(request, f'🗑 «{name}» удалён.')
        return redirect('people:person_list')
    return render(request, 'people/person_confirm_delete.html', {'person': person})


# ─── Relationships ─────────────────────────────────────────────────────────────

@require_app_access('people')
def person_add_relationship(request, pk):
    person = get_object_or_404(Person, pk=pk)
    if request.method == 'POST':
        form = PersonRelationshipForm(request.POST)
        if form.is_valid():
            rel = form.save(commit=False)
            rel.from_person = person
            rel.save()
            messages.success(request, '✅ Связь добавлена.')
            return redirect('people:person_detail', pk=person.pk)
    else:
        form = PersonRelationshipForm()
    return render(request, 'people/relationship_form.html', {'form': form, 'person': person})


@require_app_access('people')
def relationship_delete(request, pk):
    rel = get_object_or_404(PersonRelationship, pk=pk)
    person_pk = rel.from_person_id
    rel.delete()
    messages.success(request, '🗑 Связь удалена.')
    return redirect('people:person_detail', pk=person_pk)


# ─── Families ──────────────────────────────────────────────────────────────────

@require_app_access('people')
def family_list(request):
    q = request.GET.get('q', '').strip()
    families = Family.objects.prefetch_related('members__person', 'members__role')
    if q:
        families = families.filter(name__icontains=q)
    return render(request, 'people/family_list.html', {'families': families, 'q': q})


@require_app_access('people')
def family_detail(request, pk):
    family  = get_object_or_404(Family, pk=pk)
    members = family.members.select_related('person', 'role').order_by('-is_head', 'person__full_name')
    return render(request, 'people/family_detail.html', {'family': family, 'members': members})


@require_app_access('people')
def family_create(request):
    if request.method == 'POST':
        form = FamilyForm(request.POST)
        if form.is_valid():
            family = form.save()
            messages.success(request, f'✅ Семья «{family.name}» создана.')
            return redirect('people:family_detail', pk=family.pk)
    else:
        form = FamilyForm()
    return render(request, 'people/family_form.html', {'form': form, 'action': 'Создать семью'})


@require_app_access('people')
def family_edit(request, pk):
    family = get_object_or_404(Family, pk=pk)
    if request.method == 'POST':
        form = FamilyForm(request.POST, instance=family)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Данные семьи обновлены.')
            return redirect('people:family_detail', pk=family.pk)
    else:
        form = FamilyForm(instance=family)
    return render(request, 'people/family_form.html', {'form': form, 'action': 'Редактировать', 'family': family})


@require_app_access('people')
def family_delete(request, pk):
    family = get_object_or_404(Family, pk=pk)
    if request.method == 'POST':
        name = family.name
        family.delete()
        messages.success(request, f'🗑 Семья «{name}» удалена.')
        return redirect('people:family_list')
    return render(request, 'people/family_confirm_delete.html', {'family': family})


@require_app_access('people')
def family_add_member(request, pk):
    family = get_object_or_404(Family, pk=pk)
    if request.method == 'POST':
        form = FamilyMemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.family = family
            try:
                member.full_clean()
                member.save()
                messages.success(request, f'✅ {member.person.full_name} добавлен в семью.')
            except Exception as e:
                messages.error(request, str(e))
            return redirect('people:family_detail', pk=family.pk)
    else:
        form = FamilyMemberForm()
    return render(request, 'people/member_form.html', {'form': form, 'family': family})


@require_app_access('people')
def family_remove_member(request, family_pk, person_pk):
    member = get_object_or_404(FamilyMember, family_id=family_pk, person_id=person_pk)
    member.delete()
    messages.success(request, '🗑 Участник удалён из семьи.')
    return redirect('people:family_detail', pk=family_pk)
