import mimetypes

from django.db import connection
from django.http import FileResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
import requests
import math
from django.conf import settings
from .models import CHIDrugFormularyEntry, DermoscopySubmission, ModelTrainingSubmission
from .serializers import (
    CHIDrugFormularySerializer,
    DermoscopyPredictionInputSerializer,
    DermoscopySubmissionSerializer,
    ElectrosurgeryCaseSerializer,
    ModelTrainingSubmissionSerializer,
)

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


class DermoscopySubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = DermoscopySubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        queryset = DermoscopySubmission.objects.select_related('submitted_by')
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(submitted_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user, status='Model unavailable')

    @action(detail=True, methods=['get'], url_path='image')
    def image_file(self, request, pk=None):
        submission = self.get_object()
        content_type = mimetypes.guess_type(submission.image.name)[0] or 'application/octet-stream'
        response = FileResponse(submission.image.open('rb'), content_type=content_type)
        response['Cache-Control'] = 'private, no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        return response


class DermoscopyModelStatusView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            response = requests.get(f'{settings.DERMOSCOPY_MODEL_API_URL}/health', timeout=8)
            response.raise_for_status()
        except requests.RequestException:
            return Response({
                'available': False,
                'provider': 'JavariaRizwan/HAM10000_API',
                'detail': 'The hosted model is unavailable or starting. Try again shortly.',
            })
        return Response({
            'available': True,
            'provider': 'JavariaRizwan/HAM10000_API',
            'classes': [
                'Actinic keratoses', 'Basal cell carcinoma', 'Benign keratosis-like lesions',
                'Dermatofibroma', 'Melanocytic nevi', 'Melanoma', 'Vascular lesions',
            ],
        })


class DermoscopyPredictionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DermoscopyPredictionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image = serializer.validated_data['image']
        try:
            result = requests.post(
                f'{settings.DERMOSCOPY_MODEL_API_URL}/predict',
                files={'file': (image.name, image.read(), image.content_type)},
                timeout=(5, 90),
            )
            result.raise_for_status()
            prediction = result.json()
        except requests.Timeout:
            return Response({'detail': 'The hosted model timed out. It may be starting; try again shortly.'}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except (requests.RequestException, ValueError):
            return Response({'detail': 'The hosted model is unavailable or returned an invalid response.'}, status=status.HTTP_502_BAD_GATEWAY)

        predicted_class = prediction.get('predicted_class')
        confidence = prediction.get('confidence')
        probabilities = prediction.get('all_probabilities')
        if (
            not isinstance(predicted_class, str)
            or not isinstance(confidence, (int, float))
            or not math.isfinite(confidence)
            or not 0 <= confidence <= 1
            or not isinstance(probabilities, dict)
        ):
            return Response({'detail': 'The hosted model returned an invalid prediction.'}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({
            'predicted_class': predicted_class,
            'confidence': confidence,
            'all_probabilities': probabilities,
            'provider': 'JavariaRizwan/HAM10000_API',
            'disclaimer': prediction.get('disclaimer', 'Research output only. Not a medical diagnosis.'),
        })


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            connection.ensure_connection()
        except Exception:
            return Response({'status': 'unavailable'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({'status': 'ok'})


class ClinicianLoginView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is None or not user.is_active or (not user.is_superuser and not user.is_verified_clinician):
            return Response({'detail': 'Invalid credentials or clinician account is not enabled.'}, status=status.HTTP_401_UNAUTHORIZED)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'username': user.get_username()})


class ClinicianLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClinicalProtocolView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, protocol):
        supported_protocols = {'cryotherapy', 'electrosurgery', 'laser', 'fillers', 'botox', 'uvb'}
        if protocol not in supported_protocols:
            return Response({'detail': 'Unknown protocol.'}, status=status.HTTP_404_NOT_FOUND)
        if protocol == 'electrosurgery':
            serializer = ElectrosurgeryCaseSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
        return Response({
            'status': 'not_configured',
            'detail': 'No verified protocol source is configured. Power, anaesthesia, and Arabic instructions were not generated.',
        }, status=status.HTTP_501_NOT_IMPLEMENTED)