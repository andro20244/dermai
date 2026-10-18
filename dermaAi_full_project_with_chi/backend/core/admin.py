from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import ClinicianUser, DermoscopySubmission


@admin.register(ClinicianUser)
class ClinicianUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'specialty', 'is_verified_clinician', 'is_staff')
    list_filter = ('is_verified_clinician', 'is_staff')
    search_fields = ('username', 'email')
    fieldsets = UserAdmin.fieldsets + (
        ('Clinical access', {'fields': ('specialty', 'is_verified_clinician')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Clinical access', {'fields': ('specialty', 'is_verified_clinician')}),
    )


@admin.register(DermoscopySubmission)
class DermoscopySubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'localization', 'confirmed_diagnosis', 'status', 'consent_for_training', 'submitted_by', 'submitted_at')
    list_filter = ('status', 'consent_for_training', 'skin_phototype')
    search_fields = ('localization', 'clinical_notes', 'submitted_by__username')
    readonly_fields = ('submitted_at', 'image_review_link')
    fields = (
        'image_review_link', 'age', 'sex', 'skin_phototype', 'localization', 'confirmed_diagnosis',
        'clinical_notes', 'consent_for_training', 'status', 'submitted_by', 'submitted_at',
    )

    @admin.display(description='Private image review')
    def image_review_link(self, submission):
        return format_html('<a href="/api/v1/dermoscopy/submissions/{}/image/">Open submitted image</a>', submission.pk)