import gzip
import shutil
import sqlite3
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import CHIDrugFormularyEntry


class Command(BaseCommand):
    help = 'Import the bundled CHI formulary into an empty application database.'

    def handle(self, *args, **options):
        if CHIDrugFormularyEntry.objects.exists():
            self.stdout.write('Formulary already contains data; skipping import.')
            return

        seed_path = Path(settings.BASE_DIR) / 'chi_formulary_seed.sqlite3.gz'
        if not seed_path.is_file():
            raise CommandError(f'Formulary seed file not found: {seed_path}')

        field_names = (
            'indication', 'icd_10_code', 'pharmacological_class', 'scientific_name',
            'pharmaceutical_form', 'administration_route', 'strength', 'strength_unit',
            'mdd_adults', 'notes',
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / 'seed.sqlite3'
            with gzip.open(seed_path, 'rb') as compressed_seed, database_path.open('wb') as seed_file:
                shutil.copyfileobj(compressed_seed, seed_file)

            source = sqlite3.connect(database_path)
            try:
                rows = source.execute(
                    'SELECT indication, icd_10_code, pharmacological_class, scientific_name, '
                    'pharmaceutical_form, administration_route, strength, strength_unit, mdd_adults, notes '
                    'FROM core_chidrugformularyentry'
                )
                imported = 0
                with transaction.atomic():
                    while batch := rows.fetchmany(1000):
                        CHIDrugFormularyEntry.objects.bulk_create(
                            [CHIDrugFormularyEntry(**dict(zip(field_names, row))) for row in batch],
                            batch_size=1000,
                        )
                        imported += len(batch)
            except sqlite3.Error as error:
                raise CommandError(f'Could not read formulary seed data: {error}') from error
            finally:
                source.close()

        self.stdout.write(self.style.SUCCESS(f'Imported {imported:,} CHI formulary entries.'))