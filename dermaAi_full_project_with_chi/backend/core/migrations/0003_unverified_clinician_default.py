from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_dermoscopysubmission'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clinicianuser',
            name='is_verified_clinician',
            field=models.BooleanField(default=False),
        ),
    ]