from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
	CHIDrugFormularyViewSet,
	ClinicianLoginView,
	ClinicianLogoutView,
	ClinicalProtocolView,
	DermoscopyModelStatusView,
	DermoscopyPredictionView,
	CryotherapyViewSet,
	DermoscopySubmissionViewSet,
	HealthCheckView,
	ModelTrainingSubmissionViewSet,
)

router = DefaultRouter()
router.register(r'formulary', CHIDrugFormularyViewSet, basename='chi-formulary')
router.register(r'cryotherapy', CryotherapyViewSet, basename='cryotherapy')
router.register(r'dermoscopy/submissions', DermoscopySubmissionViewSet, basename='dermoscopy-submission')
router.register(r'train-model', ModelTrainingSubmissionViewSet, basename='train-model')

urlpatterns = [
	path('health/', HealthCheckView.as_view(), name='health'),
	path('auth/login/', ClinicianLoginView.as_view(), name='clinician-login'),
	path('auth/logout/', ClinicianLogoutView.as_view(), name='clinician-logout'),
	path('protocols/<slug:protocol>/', ClinicalProtocolView.as_view(), name='clinical-protocol'),
	path('dermoscopy/model-status/', DermoscopyModelStatusView.as_view(), name='dermoscopy-model-status'),
	path('dermoscopy/predict/', DermoscopyPredictionView.as_view(), name='dermoscopy-predict'),
	path('', include(router.urls)),
]