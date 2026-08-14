"""Command to load ingredients from a data file."""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient

DEFAULT_PATH = settings.BASE_DIR / 'data' / 'ingredients.json'


class Command(BaseCommand):
    """Load ingredients from a JSON file into the database."""

    help = 'Load ingredients from a JSON file into the database.'

    def add_arguments(self, parser):
        """Add an optional file path argument."""
        parser.add_argument(
            '--path',
            default=str(DEFAULT_PATH),
            help='Path to the ingredients JSON file.',
        )

    def handle(self, *args, **options):
        """Read the file and save ingredients idempotently."""
        path = Path(options['path'])
        if not path.exists():
            raise FileNotFoundError(f'Ingredients file not found: {path}')
        with path.open(encoding='utf-8') as file:
            items = json.load(file)
        created = 0
        for item in items:
            _, was_created = Ingredient.objects.get_or_create(
                name=item['name'],
                measurement_unit=item['measurement_unit'],
            )
            created += int(was_created)
        self.stdout.write(
            self.style.SUCCESS(
                f'Created {created} ingredients, '
                f'{len(items) - created} already existed.'
            )
        )
