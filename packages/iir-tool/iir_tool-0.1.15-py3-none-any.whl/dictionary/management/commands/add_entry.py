import sys
from django.core.management.base import BaseCommand, CommandError
from dictionary.models import Entry


class Command(BaseCommand):
    help = "Add Entry records from stdin for the given category."

    def add_arguments(self, parser):
        parser.add_argument("category", type=str, help="Category for the entries")

    def handle(self, *args, **options):
        category = options.get("category")
        if not category:
            raise CommandError("Category is required")

        created_count = 0
        for raw_line in self._read_lines():
            value = raw_line.strip()
            if not value:
                continue
            _, created = Entry.objects.get_or_create(
                category=category, value=value, defaults={"is_active": True}
            )
            if created:
                created_count += 1

        self.stdout.write(f"Added {created_count} entries to category '{category}'")

    def _read_lines(self):
        for line in sys.stdin:
            yield line
