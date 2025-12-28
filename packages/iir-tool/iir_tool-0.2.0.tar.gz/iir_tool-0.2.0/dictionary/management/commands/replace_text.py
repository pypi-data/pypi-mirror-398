import sys

from django.core.management.base import BaseCommand

from dictionary.models import Entry
from dictionary.services.replacement_internal import (
    replace_text_internal,
    replace_text_internal_with_counts,
)


class Command(BaseCommand):
    help = "Replace internal identifiers from stdin and write the result to stdout."

    def add_arguments(self, parser):
        parser.add_argument(
            "--category",
            action="append",
            dest="categories",
            default=[],
            help="Limit replacement to the given category (can be specified multiple times).",
        )
        parser.add_argument(
            "--exclude",
            action="append",
            dest="excludes",
            default=[],
            help="Exclude categories from replacement (ignored if --category is set).",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            dest="use_all",
            default=False,
            help="Include all categories (default behavior when no filters are provided).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help="Do not output replaced text; print replacement counts to stderr.",
        )

    def handle(self, *args, **options):
        stdin_text = sys.stdin.read()

        categories = self._resolve_categories(
            options.get("categories") or [],
            options.get("excludes") or [],
            use_all=options.get("use_all", False),
        )

        if options.get("dry_run"):
            _, counts = replace_text_internal_with_counts(
                stdin_text, include_categories=categories
            )
            for category in sorted(counts.keys()):
                self.stderr.write(f"{category}: {counts[category]}")
            return

        output = replace_text_internal(
            stdin_text, include_categories=categories
        )
        self.stdout.write(output, ending="")

    def _resolve_categories(self, categories, excludes, use_all=False):
        if categories:
            return set(categories)

        active_categories = set(
            Entry.objects.filter(is_active=True)
            .values_list("category", flat=True)
            .distinct()
        )

        if not use_all and excludes:
            active_categories -= set(excludes)

        return active_categories
