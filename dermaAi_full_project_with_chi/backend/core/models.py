from django.contrib.auth.models import AbstractUser
from django.db import models

class ClinicianUser(AbstractUser):
    specialty = models.CharField(max_length=100, default='Dermatology')
    is_verified_clinician = models.BooleanField(default=True)

class PatientCase(models.Model):
    patient_id = models.CharField(max_length=50, unique=True)
    age = models.PositiveIntegerField()
    sex = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    skin_phototype = models.CharField(max_length=5, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class DermoscopyAnalysis(models.Model):
    patient = models.ForeignKey(PatientCase, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='dermoscopy/')
    localization = models.CharField(max_length=100)
    predicted_class = models.CharField(max_length=100)
    confidence = models.FloatField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class CHIDrugFormularyEntry(models.Model):
    indication = models.CharField(max_length=255, db_index=True)
    icd_10_code = models.CharField(max_length=20, db_index=True)
    pharmacological_class = models.CharField(max_length=255)
    scientific_name = models.CharField(max_length=255, db_index=True)
    pharmaceutical_form = models.CharField(max_length=100)
    administration_route = models.CharField(max_length=100)
    strength = models.CharField(max_length=50)
    strength_unit = models.CharField(max_length=20)
    mdd_adults = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

class ModelTrainingSubmission(models.Model):
    image = models.ImageField(upload_to='training_dataset/')
    confirmed_diagnosis = models.CharField(max_length=255)
    description_notes = models.TextField()
    submitted_by = models.ForeignKey(ClinicianUser, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=50, default='Pending Review')
    submitted_at = models.DateTimeField(auto_now_add=True)