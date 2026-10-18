from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import CHIDrugFormularyEntry, ModelTrainingSubmission
from .serializers import (
    CHIDrugFormularySerializer, DosageCalculationInputSerializer,
    CryotherapyRequestSerializer, ModelTrainingSubmissionSerializer
)

class CHIDrugFormularyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CHIDrugFormularyEntry.objects.all()
    serializer_class = CHIDrugFormularySerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'], url_path='search-by-diagnosis')
    def search_by_diagnosis(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'error': 'Query parameter "q" is required.'}, status=status.HTTP_400_BAD_REQUEST)
        results = self.queryset.filter(Q(indication__icontains=query) | Q(icd_10_code__iexact=query))
        serializer = self.get_serializer(results, many=True)
        return Response({'query': query, 'count': results.count(), 'recommendations': serializer.data})

    @action(detail=False, methods=['post'], url_path='calculate-dosage')
    def calculate_dosage(self, request):
        serializer = DosageCalculationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        weight = data['weight_kg']
        egfr = data['egfr']
        base_mg = min(15.0, weight * 0.2)
        if egfr < 60:
            base_mg *= 0.75
        return Response({
            'drug_name': data['drug_name'].title(),
            'disease': data['disease'].title(),
            'calculated_dose': f"{round(base_mg, 1)} mg",
            'frequency': 'Once weekly',
            'safety_warnings': ['Monitor renal function and LFTs every 4-6 weeks.']
        })

class CryotherapyViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    def create(self, request):
        serializer = CryotherapyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return Response({
            'protocol': {'freeze_time_seconds': 10, 'thaw_time_seconds': 30, 'cycles': 2},
            'instructions': {'en': {'pre': 'Avoid topicals 24h prior.', 'post': 'Keep clean and dry.'},
                             'ar': {'pre': 'تجنب الكريمات قبل 24 ساعة.', 'post': 'حافظ على المنطقة نظيفة وجافة.'}}
        })

class ModelTrainingSubmissionViewSet(viewsets.ModelViewSet):
    queryset = ModelTrainingSubmission.objects.all().order_by('-submitted_at')
    serializer_class = ModelTrainingSubmissionSerializer
    permission_classes = [permissions.AllowAny]