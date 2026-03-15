from decimal import Decimal
from collections import OrderedDict

from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Prefetch, DecimalField, Value
from django.db.models.functions import Coalesce

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from .models import Project, BudgetSection, BudgetCategory, Expense, BudgetCorrection
from .export import export_project_to_excel

MONEY = DecimalField(max_digits=14, decimal_places=2)


def _cat_spent():
    return Coalesce(Sum('expenses__amount'), Value(Decimal('0')), output_field=MONEY)

def _proj_spent():
    return Coalesce(Sum('categories__expenses__amount'), Value(Decimal('0')), output_field=MONEY)

def _sec_allocated():
    return Coalesce(Sum('categories__allocated_amount'), Value(Decimal('0')), output_field=MONEY)

def _sec_spent():
    return Coalesce(Sum('categories__expenses__amount'), Value(Decimal('0')), output_field=MONEY)


def has_budget_access(user):
    return user.is_superuser or user.app_access in ('budget', 'all')

def can_edit(user):
    return user.is_superuser or user.role in ('admin', 'editor')


# ── Serializers ───────────────────────────────────────────────────────────────

class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_code = serializers.CharField(source='category.code', read_only=True)
    created_by    = serializers.StringRelatedField(read_only=True)

    class Meta:
        model  = Expense
        fields = (
            'id', 'category', 'category_name', 'category_code',
            'quantity', 'amount', 'date', 'description',
            'document_number', 'period', 'created_by', 'created_at',
        )
        read_only_fields = ('id', 'created_by', 'created_at')


class CorrectionSerializer(serializers.ModelSerializer):
    correction_type_display = serializers.CharField(source='get_correction_type_display', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    created_by    = serializers.StringRelatedField(read_only=True)

    class Meta:
        model  = BudgetCorrection
        fields = (
            'id', 'correction_type', 'correction_type_display',
            'category', 'category_name', 'old_value', 'new_value',
            'reason', 'date', 'created_by', 'created_at',
        )
        read_only_fields = ('id', 'created_by', 'created_at')


class CategorySerializer(serializers.ModelSerializer):
    total_spent   = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, default=0)
    remaining     = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, default=0)
    spent_percent = serializers.IntegerField(read_only=True, default=0)
    is_over_budget = serializers.BooleanField(read_only=True, default=False)
    is_warning    = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model  = BudgetCategory
        fields = (
            'id', 'section', 'code', 'name', 'unit_measure',
            'quantity', 'unit_cost', 'frequency', 'allocated_amount',
            'notes', 'order', 'total_spent', 'remaining',
            'spent_percent', 'is_over_budget', 'is_warning',
        )


class SectionSerializer(serializers.ModelSerializer):
    categories    = CategorySerializer(many=True, read_only=True)
    total_allocated = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, default=0)
    total_spent   = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, default=0)

    class Meta:
        model  = BudgetSection
        fields = ('id', 'code', 'name', 'order', 'total_allocated', 'total_spent', 'categories')


class ProjectListSerializer(serializers.ModelSerializer):
    total_spent   = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, default=0)
    total_remaining = serializers.SerializerMethodField()
    spent_percent = serializers.SerializerMethodField()
    duration_months = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Project
        fields = (
            'id', 'name', 'project_code', 'donor', 'status',
            'start_date', 'end_date', 'total_budget', 'currency',
            'total_spent', 'total_remaining', 'spent_percent',
            'duration_months', 'completed_at',
        )

    def get_total_remaining(self, obj):
        return obj.total_budget - (obj.__dict__.get('total_spent') or Decimal('0'))

    def get_spent_percent(self, obj):
        spent = obj.__dict__.get('total_spent') or Decimal('0')
        if not obj.total_budget:
            return 0
        return int(spent / obj.total_budget * 100)


class ProjectDetailSerializer(ProjectListSerializer):
    sections = SectionSerializer(many=True, read_only=True)
    completion_note = serializers.CharField(read_only=True)

    class Meta(ProjectListSerializer.Meta):
        fields = ProjectListSerializer.Meta.fields + ('description', 'sections', 'completion_note', 'created_at')


# ── Views ─────────────────────────────────────────────────────────────────────

class ProjectListView(APIView):
    """GET /api/budget/projects/  POST /api/budget/projects/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not has_budget_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)

        projects = Project.objects.annotate(total_spent=_proj_spent())
        return Response(ProjectListSerializer(projects, many=True).data)

    def post(self, request):
        if not can_edit(request.user):
            return Response({'detail': 'Нет прав на создание.'}, status=403)

        s = ProjectWriteSerializer(data=request.data)
        if s.is_valid():
            project = s.save(created_by=request.user)
            return Response(ProjectListSerializer(project).data, status=201)
        return Response(s.errors, status=400)


class ProjectWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Project
        fields = ('name', 'project_code', 'donor', 'start_date', 'end_date',
                  'total_budget', 'currency', 'description')


class ProjectDetailView(APIView):
    """GET/PATCH /api/budget/projects/:pk/"""
    permission_classes = [IsAuthenticated]

    def _get_project(self, pk):
        cat_qs = BudgetCategory.objects.annotate(total_spent=_cat_spent())
        sec_qs = BudgetSection.objects.annotate(
            total_allocated=_sec_allocated(),
            total_spent=_sec_spent(),
        ).prefetch_related(Prefetch('categories', queryset=cat_qs))

        return (
            Project.objects
            .annotate(total_spent=_proj_spent())
            .prefetch_related(Prefetch('sections', queryset=sec_qs))
            .get(pk=pk)
        )

    def get(self, request, pk):
        if not has_budget_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        try:
            project = self._get_project(pk)
        except Project.DoesNotExist:
            return Response({'detail': 'Не найден.'}, status=404)
        return Response(ProjectDetailSerializer(project).data)

    def patch(self, request, pk):
        if not can_edit(request.user):
            return Response({'detail': 'Нет прав.'}, status=403)
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'detail': 'Не найден.'}, status=404)
        s = ProjectWriteSerializer(project, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(ProjectListSerializer(
                Project.objects.annotate(total_spent=_proj_spent()).get(pk=pk)
            ).data)
        return Response(s.errors, status=400)


class ProjectExpensesView(APIView):
    """GET /api/budget/projects/:pk/expenses/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if not has_budget_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        expenses = (
            Expense.objects
            .filter(category__project_id=pk)
            .select_related('category', 'created_by')
            .order_by('-date', '-created_at')
        )
        return Response(ExpenseSerializer(expenses, many=True).data)


class ProjectCorrectionsView(APIView):
    """GET /api/budget/projects/:pk/corrections/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if not has_budget_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        corrections = (
            BudgetCorrection.objects
            .filter(project_id=pk)
            .select_related('category', 'created_by')
            .order_by('-created_at')
        )
        return Response(CorrectionSerializer(corrections, many=True).data)


class ProjectCompleteView(APIView):
    """POST /api/budget/projects/:pk/complete/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not can_edit(request.user):
            return Response({'detail': 'Нет прав.'}, status=403)
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'detail': 'Не найден.'}, status=404)
        note = request.data.get('completion_note', '')
        project.complete(request.user, note)
        return Response({'detail': 'Проект завершён.'})


class ExportExcelView(APIView):
    """GET /api/budget/projects/:pk/export/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if not has_budget_access(request.user):
            return Response({'detail': 'Нет доступа.'}, status=403)
        try:
            project = Project.objects.prefetch_related(
                'sections__categories__expenses'
            ).get(pk=pk)
        except Project.DoesNotExist:
            return Response({'detail': 'Не найден.'}, status=404)

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        fname = f"budget_{project.project_code or pk}_{timezone.now().strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{fname}"'
        export_project_to_excel(project, response)
        return response


class ExpenseCreateView(APIView):
    """POST /api/budget/expenses/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not can_edit(request.user):
            return Response({'detail': 'Нет прав.'}, status=403)
        s = ExpenseSerializer(data=request.data)
        if s.is_valid():
            expense = s.save(created_by=request.user)
            return Response(ExpenseSerializer(expense).data, status=201)
        return Response(s.errors, status=400)


class ExpenseDetailView(APIView):
    """PATCH/DELETE /api/budget/expenses/:pk/"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not can_edit(request.user):
            return Response({'detail': 'Нет прав.'}, status=403)
        try:
            expense = Expense.objects.get(pk=pk)
        except Expense.DoesNotExist:
            return Response({'detail': 'Не найден.'}, status=404)
        s = ExpenseSerializer(expense, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(ExpenseSerializer(expense).data)
        return Response(s.errors, status=400)

    def delete(self, request, pk):
        if not can_edit(request.user):
            return Response({'detail': 'Нет прав.'}, status=403)
        try:
            Expense.objects.get(pk=pk).delete()
        except Expense.DoesNotExist:
            return Response({'detail': 'Не найден.'}, status=404)
        return Response(status=204)


class CategoryCreateView(APIView):
    """POST /api/budget/categories/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not can_edit(request.user):
            return Response({'detail': 'Нет прав.'}, status=403)
        s = CategoryWriteSerializer(data=request.data)
        if s.is_valid():
            cat = s.save()
            return Response(CategorySerializer(cat).data, status=201)
        return Response(s.errors, status=400)


class CategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BudgetCategory
        fields = ('project', 'section', 'code', 'name', 'unit_measure',
                  'quantity', 'unit_cost', 'frequency', 'allocated_amount', 'notes', 'order')


class CategoryDetailView(APIView):
    """PATCH /api/budget/categories/:pk/"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not can_edit(request.user):
            return Response({'detail': 'Нет прав.'}, status=403)
        try:
            cat = BudgetCategory.objects.get(pk=pk)
        except BudgetCategory.DoesNotExist:
            return Response({'detail': 'Не найден.'}, status=404)
        s = CategoryWriteSerializer(cat, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(CategorySerializer(
                BudgetCategory.objects.annotate(total_spent=_cat_spent()).get(pk=pk)
            ).data)
        return Response(s.errors, status=400)


class CorrectionCreateView(APIView):
    """POST /api/budget/corrections/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not can_edit(request.user):
            return Response({'detail': 'Нет прав.'}, status=403)
        s = CorrectionWriteSerializer(data=request.data)
        if s.is_valid():
            correction = s.save(created_by=request.user)
            # Применить изменение суммы если указана категория
            if correction.correction_type == 'amount' and correction.category:
                try:
                    correction.category.allocated_amount = Decimal(correction.new_value)
                    correction.category.save()
                except Exception:
                    pass
            return Response(CorrectionSerializer(correction).data, status=201)
        return Response(s.errors, status=400)


class CorrectionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BudgetCorrection
        fields = ('project', 'category', 'correction_type', 'old_value', 'new_value', 'reason', 'date')
