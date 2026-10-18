from rest_framework import serializers
from .models import CHIDrugFormularyEntry, ModelTrainingSubmission

class CHIDrugFormularySerializer(serializers.ModelSerializer):
    class Meta:
        model = CHIDrugFormularyEntry
        fields = '__all__'

class DosageCalculationInputSerializer(serializers.Serializer):
    drug_name = serializers.CharField(max_length=255)
    disease = serializers.CharField(max_length=255)
    age = serializers.IntegerField(min_value=0)
    weight_kg = serializers.FloatField(min_value=0.5)
    egfr = serializers.FloatField(required=False, default=90.0)
    clinical_notes = serializers.CharField(required=False, allow_blank=True, default='')

class CryotherapyRequestSerializer(serializers.Serializer):
    age = serializers.IntegerField(min_value=0)
    site = serializers.CharField(max_length=100)
    disease = serializers.CharField(max_length=100)
    lesion_type = serializers.CharField(max_length=100)

class ModelTrainingSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelTrainingSubmission
        fields = ['id', 'image', 'confirmed_diagnosis', 'description_notes', 'submitted_by', 'status', 'submitted_at']
        read_only_fields = ['submitted_by', 'status', 'submitted_at']