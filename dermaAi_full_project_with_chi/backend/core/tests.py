from io import BytesIO
from pathlib import Path
import shutil
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from core.models import CHIDrugFormularyEntry, DermoscopySubmission


TEST_MEDIA_ROOT = '/tmp/dermaai-test-media'


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ClinicalApiTests(TestCase):
    def setUp(self):
        Path(TEST_MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
        self.client = APIClient()
        self.clinician = get_user_model().objects.create_user(
            username='dermatologist',
            password='test-only-password',
            is_verified_clinician=True,
        )

    def tearDown(self):
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def image_upload(self):
        image = Image.new('RGB', (8, 8), color=(120, 80, 60))
        image_file = BytesIO()
        image.save(image_file, format='JPEG')
        from django.core.files.uploadedfile import SimpleUploadedFile

        return SimpleUploadedFile('lesion.jpg', image_file.getvalue(), content_type='image/jpeg')

    def submission_payload(self, **extra):
        return {
            'image': self.image_upload(),
            'localization': 'left forearm',
            'age': 42,
            **extra,
        }

    def test_unverified_clinician_cannot_sign_in(self):
        self.clinician.is_verified_clinician = False
        self.clinician.save(update_fields=['is_verified_clinician'])

        response = self.client.post('/api/v1/auth/login/', {
            'username': 'dermatologist',
            'password': 'test-only-password',
        })

        self.assertEqual(response.status_code, 401)

    def test_training_consent_requires_confirmed_diagnosis(self):
        self.client.force_authenticate(self.clinician)

        response = self.client.post(
            '/api/v1/dermoscopy/submissions/',
            self.submission_payload(consent_for_training=True),
            format='multipart',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('confirmed_diagnosis', response.data)
        self.assertEqual(DermoscopySubmission.objects.count(), 0)

    def test_clinician_can_save_consented_case_and_review_private_image(self):
        self.client.force_authenticate(self.clinician)

        response = self.client.post(
            '/api/v1/dermoscopy/submissions/',
            self.submission_payload(
                confirmed_diagnosis='Benign nevus',
                consent_for_training=True,
            ),
            format='multipart',
        )

        self.assertEqual(response.status_code, 201, response.data)
        case = DermoscopySubmission.objects.get(pk=response.data['id'])
        self.assertTrue(case.consent_for_training)
        self.assertEqual(case.confirmed_diagnosis, 'Benign nevus')

        image_response = self.client.get(f'/api/v1/dermoscopy/submissions/{case.pk}/image/')
        self.assertEqual(image_response.status_code, 200)
        self.assertEqual(image_response['Cache-Control'], 'private, no-store')

    def test_diagnosis_based_formulary_search(self):
        CHIDrugFormularyEntry.objects.create(
            indication='ECZEMA',
            icd_10_code='L30.9',
            pharmacological_class='Topical corticosteroid',
            scientific_name='EXAMPLE MEDICINE',
            pharmaceutical_form='Cream',
            administration_route='Topical',
            strength='1',
            strength_unit='%',
        )

        response = self.client.get('/api/v1/formulary/search-by-diagnosis/?q=ECZEMA')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['scientific_name'], 'EXAMPLE MEDICINE')

    def test_procedure_parameters_are_not_generated(self):
        self.client.force_authenticate(self.clinician)

        response = self.client.post('/api/v1/protocols/electrosurgery/', {
            'age': 42,
            'sex': 'Female',
            'disease': 'Benign lesion',
            'site': 'Forearm',
            'lesion_type': 'Papule',
            'lesion_count': 2,
            'device_type': 'Not recorded',
        }, format='json')

        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.data['status'], 'not_configured')
        self.assertIn('Power', response.data['detail'])

    def test_electrosurgery_requires_lesion_count(self):
        self.client.force_authenticate(self.clinician)

        response = self.client.post('/api/v1/protocols/electrosurgery/', {
            'age': 42,
            'sex': 'Female',
            'disease': 'Benign lesion',
            'site': 'Forearm',
            'lesion_type': 'Papule',
            'device_type': 'Not recorded',
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('lesion_count', response.data)

    def test_prediction_requires_explicit_external_processing_consent(self):
        self.client.force_authenticate(self.clinician)

        response = self.client.post('/api/v1/dermoscopy/predict/', {
            'image': self.image_upload(),
            'consent_to_external_processing': False,
        }, format='multipart')

        self.assertEqual(response.status_code, 400)
        self.assertIn('consent_to_external_processing', response.data)

    @patch('core.views.requests.post')
    def test_prediction_proxy_returns_validated_hosted_result(self, mocked_post):
        self.client.force_authenticate(self.clinician)
        mocked_response = Mock()
        mocked_response.raise_for_status.return_value = None
        mocked_response.json.return_value = {
            'predicted_class': 'Melanocytic nevi',
            'confidence': 0.81,
            'all_probabilities': {'Melanocytic nevi': 0.81, 'Melanoma': 0.19},
            'disclaimer': 'Research output only.',
        }
        mocked_post.return_value = mocked_response

        response = self.client.post('/api/v1/dermoscopy/predict/', {
            'image': self.image_upload(),
            'consent_to_external_processing': True,
        }, format='multipart')

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['predicted_class'], 'Melanocytic nevi')
        mocked_post.assert_called_once()