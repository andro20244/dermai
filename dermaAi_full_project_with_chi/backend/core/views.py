from django.db import connection
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from .models import CHIDrugFormularyEntry, ModelTrainingSubmission
from .serializers import CHIDrugFormularySerializer, ModelTrainingSubmissionSerializer

class CHIDrugFormularyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CHIDrugFormularyEntry.objects.order_by('indication', 'scientific_name', 'strength')
    serializer_class = CHIDrugFormularySerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'], url_path='search-by-diagnosis')
    def search_by_diagnosis(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'error': 'Query parameter "q" is required.'}, status=status.HTTP_400_BAD_REQUEST)
        results = self.queryset.filter(
            Q(indication__icontains=query)
            | Q(icd_10_code__iexact=query)
            | Q(scientific_name__icontains=query)
            | Q(pharmacological_class__icontains=query)
            | Q(pharmaceutical_form__icontains=query)
        )
        page = self.paginate_queryset(results)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['post'], url_path='calculate-dosage')
    def calculate_dosage(self, request):
        return Response({
            'detail': 'Dose calculation is unavailable until drug-specific, clinically validated protocols are configured.'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)

class CryotherapyViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]
    def create(self, request):
        return Response({
            'detail': 'Procedure protocols are unavailable until indication-specific, clinically validated guidance is configured.'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)

class ModelTrainingSubmissionViewSet(viewsets.ModelViewSet):
    queryset = ModelTrainingSubmission.objects.all().order_by('-submitted_at')
    serializer_class = ModelTrainingSubmissionSerializer
    permission_classes = [permissions.IsAdminUser]


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            connection.ensure_connection()
        except Exception:
            return Response({'status': 'unavailable'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({'status': 'ok'})