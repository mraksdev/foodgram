"""Command to load default tags into the database."""

from django.core.management.base import BaseCommand

from recipes.models import Tag

TAGS = (
    ('Завтрак', 'breakfast'),
    ('Обед', 'lunch'),
    ('Ужин', 'dinner'),
)


class Command(BaseCommand):
    """Load default tags into the database."""

    help = 'Load default tags into the database.'

    def handle(self, *args, **options):
        """Create the default tags idempotently."""
        created = 0
        for name, slug in TAGS:
            _, was_created = Tag.objects.get_or_create(
                name=name,
                slug=slug,
            )
            created += int(was_created)
        already_existed = len(TAGS) - created
        message = (
            'Created ' + str(created) + ' tags, '
            + str(already_existed) + ' already existed.'
        )
        self.stdout.write(self.style.SUCCESS(message))
