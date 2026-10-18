from rest_framework import serializers
from .models import CHIDrugFormularyEntry, DermoscopySubmission, ModelTrainingSubmission


class ElectrosurgeryCaseSerializer(serializers.Serializer):
    age = serializers.IntegerField(min_value=0, max_value=120)
    sex = serializers.ChoiceField(choices=['Female', 'Male', 'Other'])
    disease = serializers.CharField(max_length=255)
    site = serializers.CharField(max_length=100)
    lesion_type = serializers.CharField(max_length=100)
    lesion_count = serializers.IntegerField(min_value=1, max_value=500)
    device_type = serializers.CharField(max_length=255)


class DermoscopyPredictionInputSerializer(serializers.Serializer):
    image = serializers.ImageField()
    consent_to_external_processing = serializers.BooleanField()

    def validate_image(self, image):
        if image.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('Image must be 10 MB or smaller.')
        if image.content_type not in {'image/jpeg', 'image/png'}:
            raise serializers.ValidationError('Choose a JPEG or PNG image.')
        return image

    def validate_consent_to_external_processing(self, consent):
        if not consent:
            raise serializers.ValidationError('Explicit consent is required before sending an image to the hosted model.')
        return consent


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


class DermoscopySubmissionSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True)

    class Meta:
        model = DermoscopySubmission
        fields = [
            'id', 'image', 'age', 'sex', 'skin_phototype', 'localization',
            'confirmed_diagnosis', 'clinical_notes', 'consent_for_training', 'status', 'submitted_at',
        ]
        read_only_fields = ['status', 'submitted_at']

    def validate_image(self, image):
        if image.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('Image must be 10 MB or smaller.')
        return image

    def validate(self, attrs):
        if attrs.get('consent_for_training') and not attrs.get('confirmed_diagnosis', '').strip():
            raise serializers.ValidationError({
                'confirmed_diagnosis': 'A clinician-confirmed diagnosis is required for training consent.'
            })
        return attrs