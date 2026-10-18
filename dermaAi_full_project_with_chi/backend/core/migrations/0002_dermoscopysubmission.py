from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DermoscopySubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='dermoscopy/submissions/')),
                ('age', models.PositiveIntegerField(blank=True, null=True)),
                ('sex', models.CharField(blank=True, max_length=20)),
                ('skin_phototype', models.CharField(blank=True, max_length=5)),
                ('localization', models.CharField(max_length=100)),
                ('confirmed_diagnosis', models.CharField(blank=True, max_length=255)),
                ('clinical_notes', models.TextField(blank=True)),
                ('consent_for_training', models.BooleanField(default=False)),
                ('status', models.CharField(default='Model unavailable', max_length=50)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('submitted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-submitted_at'],
            },
        ),
    ]