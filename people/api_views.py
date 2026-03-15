from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from .models import (
    Person, Family, FamilyMember, PersonRelationship,
    FieldCategory, FieldDefinition, PersonFieldValue, RelationshipType,
)


def has_people_access(user):
    return user.is_superuser or user.app_access in ('people', 'all')

def can_edit(user):
    return user.is_superuser or user.role in ('admin', 'editor')


# ── Serializers ───────────────────────────────────────────────────────────────

class FieldDefinitionSerializer(serializers.ModelSerializer):
    choices_list = serializers.ListField(source='get_choices_list', read_only=True)

    class Meta:
        model  = FieldDefinition
        fields = ('id', 'name', 'label', 'field_type', 'choices_list',
                  'required', 'order', 'help_text')


class FieldCategorySerializer(serializers.ModelSerializer):
    fields = FieldDefinitionSerializer(many=True, read_only=True)

    class Meta:
        model  = FieldCategory
        fields = ('id', 'name', 'order', 'fields')


class FamilyMembershipSerializer(serializers.ModelSerializer):
    family_id   = serializers.IntegerField(source='family.id',   read_only=True)
    family_name = serializers.CharField(source='family.name',    read_only=True)
    role_name   = serializers.CharField(source='role.name',      read_only=True, default='')

    class Meta:
        model  = FamilyMember
        fields = ('id', 'family_id', 'family_name', 'role', 'role_name', 'is_head', 'joined')


class RelationshipOutSerializer(serializers.ModelSerializer):
    to_person         = serializers.SerializerMethodField()
    relationship_type = serializers.SerializerMethodField()

    class Meta:
        model  = PersonRelationship
        fields = ('id', 'to_person', 'relationship_type', 'note')

    def get_to_person(self, obj):
        return {'id': obj.to_person.id, 'full_name': obj.to_person.full_name}

    def get_relationship_type(self, obj):
        return {'id': obj.relationship_type.id,
                'name': obj.relationship_type.name,
                'reverse_name': obj.relationship_type.reverse_name}


class RelationshipInSerializer(serializers.ModelSerializer):
    from_person       = serializers.SerializerMethodField()
    relationship_type = serializers.SerializerMethodField()

    class Meta:
        model  = PersonRelationship
        fields = ('id', 'from_person', 'relationship_type', 'note')

    def get_from_person(self, obj):
        return {'id': obj.from_person.id, 'full_name': obj.from_person.full_name}

    def get_relationship_type(self, obj):
        return {'id': obj.relationship_type.id,
                'name': obj.relationship_type.name,
                'reverse_name': obj.relationship_type.reverse_name}


class PersonListSerializer(serializers.ModelSerializer):
    gender_display    = serializers.CharField(source='get_gender_display', read_only=True)
    age               = serializers.SerializerMethodField()
    family_memberships = FamilyMembershipSerializer(many=True, read_only=True)

    class Meta:
        model  = Person
        fields = ('id', 'full_name', 'birth_date', 'gender', 'gender_display',
                  'age', 'family_memberships')

    def get_age(self, obj):
        return obj.age()


class PersonDetailSerializer(PersonListSerializer):
    field_values       = serializers.SerializerMethodField()
    grouped_fields     = serializers.SerializerMethodField()
    relationships_from = RelationshipOutSerializer(many=True, read_only=True)
    relationships_to   = RelationshipInSerializer(many=True, read_only=True)

    class Meta(PersonListSerializer.Meta):
        fields = PersonListSerializer.Meta.fields + (
            'field_values', 'grouped_fields',
            'relationships_from', 'relationships_to',
            'created_at', 'updated_at',
        )

    def get_field_values(self, obj):
        return [
            {'field_name': fv.field.name, 'field_label': fv.field.label, 'value': fv.value}
            for fv in obj.field_values.select_related('field').all()
        ]

    def get_grouped_fields(self, obj):
        fvs = (
            obj.field_values
            .select_related('field', 'field__category')
            .order_by('field__category__order', 'field__order')
        )
        grouped = {}
        for fv in fvs:
            cat = fv.field.category.name if fv.field.category else 'Прочее'
            grouped.setdefault(cat, []).append({
                'field': FieldDefinitionSerializer(fv.field).data,
                'value': fv.value,
            })
        return grouped


class FamilyMemberDetailSerializer(serializers.ModelSerializer):
    person = serializers.SerializerMethodField()
    role   = serializers.SerializerMethodField()

    class Meta:
        model  = FamilyMember
        fields = ('id', 'person', 'role', 'is_head', 'joined', 'notes')

    def get_person(self, obj):
        from datetime import date
        age = None
        if obj.person.birth_date:
            age = (date.today() - obj.person.birth_date).days // 365
        return {
            'id': obj.person.id,
            'full_name': obj.person.full_name,
            'birth_date': obj.person.birth_date,
            'age': age,
        }

    def get_role(self, obj):
        if obj.role:
            return {'id': obj.role.id, 'name': obj.role.name}
        return None


class FamilyListSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model  = Family
        fields = ('id', 'name', 'address', 'notes', 'member_count', 'created_at')

    def get_member_count(self, obj):
        return obj.members.count()


class FamilyDetailSerializer(FamilyListSerializer):
    members = FamilyMemberDetailSerializer(many=True, read_only=True)

    class Meta(FamilyListSerializer.Meta):
        fields = FamilyListSerializer.Meta.fields + ('members',)


# ── Views ─────────────────────────────────────────────────────────────────────

class FieldCategoryListView(APIView):
    """GET /api/people/field-categories/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cats = FieldCategory.objects.prefetch_related(
            'fields'
        ).order_by('order', 'name')
        # Только активные поля
        result = []
        for cat in cats:
            fields = [f for f in cat.fields.all() if f.is_active]
            if fields:
                result.append({
                    'id': cat.id,
                    'name': cat.name,
                    'order': cat.order,
                    'fields': FieldDefinitionSerializer(fields, many=True).data,
                })
        return Response(result)


class PersonListView(APIView):
    """GET /api/people/persons/  POST /api/people/persons/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not has_people_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        q = request.query_params.get('q', '').strip()
        persons = Person.objects.prefetch_related('family_memberships__family')
        if q:
            persons = persons.filter(full_name__icontains=q)
        persons = persons.order_by('full_name')
        return Response(PersonListSerializer(persons, many=True).data)

    def post(self, request):
        if not has_people_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        data = request.data
        errors = {}
        if not data.get('full_name', '').strip():
            errors['full_name'] = ['Имя обязательно.']
        if errors:
            return Response(errors, status=400)

        person = Person.objects.create(
            full_name=data['full_name'].strip(),
            birth_date=data.get('birth_date') or None,
            gender=data.get('gender', ''),
        )
        self._save_dynamic_fields(person, data.get('field_values', {}))
        return Response(PersonDetailSerializer(self._get_person(person.pk)).data, status=201)

    def _save_dynamic_fields(self, person, field_values: dict):
        for field_name, value in field_values.items():
            try:
                fd = FieldDefinition.objects.get(name=field_name)
                PersonFieldValue.objects.update_or_create(
                    person=person, field=fd,
                    defaults={'value': str(value) if value is not None else ''},
                )
            except FieldDefinition.DoesNotExist:
                pass

    def _get_person(self, pk):
        return (
            Person.objects
            .prefetch_related(
                'family_memberships__family',
                'family_memberships__role',
                'field_values__field__category',
                'relationships_from__to_person',
                'relationships_from__relationship_type',
                'relationships_to__from_person',
                'relationships_to__relationship_type',
            )
            .get(pk=pk)
        )


class PersonDetailView(APIView):
    """GET/PATCH/DELETE /api/people/persons/:pk/"""
    permission_classes = [IsAuthenticated]

    def _get(self, pk):
        return (
            Person.objects
            .prefetch_related(
                'family_memberships__family',
                'family_memberships__role',
                'field_values__field__category',
                'relationships_from__to_person',
                'relationships_from__relationship_type',
                'relationships_to__from_person',
                'relationships_to__relationship_type',
            )
            .get(pk=pk)
        )

    def get(self, request, pk):
        if not has_people_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        try:
            return Response(PersonDetailSerializer(self._get(pk)).data)
        except Person.DoesNotExist:
            return Response({'detail': 'Не найден.'}, status=404)

    def patch(self, request, pk):
        if not has_people_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        try:
            person = Person.objects.get(pk=pk)
        except Person.DoesNotExist:
            return Response({'detail': 'Не найден.'}, status=404)

        for field in ('full_name', 'birth_date', 'gender'):
            if field in request.data:
                setattr(person, field, request.data[field] or (None if field == 'birth_date' else ''))
        person.save()

        if 'field_values' in request.data:
            for field_name, value in request.data['field_values'].items():
                try:
                    fd = FieldDefinition.objects.get(name=field_name)
                    PersonFieldValue.objects.update_or_create(
                        person=person, field=fd,
                        defaults={'value': str(value) if value is not None else ''},
                    )
                except FieldDefinition.DoesNotExist:
                    pass

        return Response(PersonDetailSerializer(self._get(pk)).data)

    def delete(self, request, pk):
        if not can_edit(request.user):
            return Response({'detail': 'Нет прав.'}, status=403)
        try:
            Person.objects.get(pk=pk).delete()
        except Person.DoesNotExist:
            return Response({'detail': 'Не найден.'}, status=404)
        return Response(status=204)


class FamilyListView(APIView):
    """GET /api/people/families/  POST /api/people/families/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not has_people_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        q = request.query_params.get('q', '').strip()
        families = Family.objects.prefetch_related('members')
        if q:
            families = families.filter(name__icontains=q)
        return Response(FamilyListSerializer(families.order_by('name'), many=True).data)

    def post(self, request):
        if not has_people_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        if not request.data.get('name', '').strip():
            return Response({'name': ['Название обязательно.']}, status=400)
        family = Family.objects.create(
            name=request.data['name'].strip(),
            address=request.data.get('address', ''),
            notes=request.data.get('notes', ''),
        )
        return Response(FamilyDetailSerializer(family).data, status=201)


class FamilyDetailView(APIView):
    """GET/PATCH/DELETE /api/people/families/:pk/"""
    permission_classes = [IsAuthenticated]

    def _get(self, pk):
        return (
            Family.objects
            .prefetch_related(
                'members__person',
                'members__role',
            )
            .get(pk=pk)
        )

    def get(self, request, pk):
        if not has_people_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        try:
            return Response(FamilyDetailSerializer(self._get(pk)).data)
        except Family.DoesNotExist:
            return Response({'detail': 'Не найдена.'}, status=404)

    def patch(self, request, pk):
        if not has_people_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        try:
            family = Family.objects.get(pk=pk)
        except Family.DoesNotExist:
            return Response({'detail': 'Не найдена.'}, status=404)
        for field in ('name', 'address', 'notes'):
            if field in request.data:
                setattr(family, field, request.data[field])
        family.save()
        return Response(FamilyDetailSerializer(self._get(pk)).data)

    def delete(self, request, pk):
        if not can_edit(request.user):
            return Response({'detail': 'Нет прав.'}, status=403)
        try:
            Family.objects.get(pk=pk).delete()
        except Family.DoesNotExist:
            return Response({'detail': 'Не найдена.'}, status=404)
        return Response(status=204)


class MemberCreateView(APIView):
    """POST /api/people/members/ — добавить человека в семью."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not has_people_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        try:
            member = FamilyMember.objects.create(
                family_id=request.data['family'],
                person_id=request.data['person'],
                role_id=request.data.get('role') or None,
                is_head=request.data.get('is_head', False),
                joined=request.data.get('joined') or None,
                notes=request.data.get('notes', ''),
            )
            return Response({'id': member.id}, status=201)
        except Exception as e:
            return Response({'detail': str(e)}, status=400)


class MemberDeleteView(APIView):
    """DELETE /api/people/members/:pk/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        if not has_people_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        try:
            FamilyMember.objects.get(pk=pk).delete()
        except FamilyMember.DoesNotExist:
            return Response({'detail': 'Не найден.'}, status=404)
        return Response(status=204)


class RelationshipCreateView(APIView):
    """POST /api/people/relationships/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not has_people_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        try:
            rel = PersonRelationship.objects.create(
                from_person_id=request.data['from_person'],
                to_person_id=request.data['to_person'],
                relationship_type_id=request.data['relationship_type'],
                note=request.data.get('note', ''),
            )
            return Response({'id': rel.id}, status=201)
        except Exception as e:
            return Response({'detail': str(e)}, status=400)


class RelationshipDeleteView(APIView):
    """DELETE /api/people/relationships/:pk/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        if not has_people_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        try:
            PersonRelationship.objects.get(pk=pk).delete()
        except PersonRelationship.DoesNotExist:
            return Response({'detail': 'Не найден.'}, status=404)
        return Response(status=204)
