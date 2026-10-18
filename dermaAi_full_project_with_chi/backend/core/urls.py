from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CHIDrugFormularyViewSet, CryotherapyViewSet, ModelTrainingSubmissionViewSet

router = DefaultRouter()
router.register(r'formulary', CHIDrugFormularyViewSet, basename='chi-formulary')
router.register(r'cryotherapy', CryotherapyViewSet, basename='cryotherapy')
router.register(r'train-model', ModelTrainingSubmissionViewSet, basename='train-model')

urlpatterns = [path('', include(router.urls))]