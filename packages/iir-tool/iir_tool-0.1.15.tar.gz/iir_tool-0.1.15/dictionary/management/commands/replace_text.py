import sys
from collections import defaultdict

from django.core.management.base import BaseCommand

from dictionary.models import Entry
from dictionary.replacement import pseudonym_for, replace


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

        entries_qs = Entry.objects.filter(is_active=True)
        if categories:
            entries_qs = entries_qs.filter(category__in=categories)
        entries = list(entries_qs)

        if options.get("dry_run"):
            _, counts = self._replace_with_counts(stdin_text, entries)
            for category in sorted(counts.keys()):
                self.stderr.write(f"{category}: {counts[category]}")
            return

        output = replace(stdin_text, entries=entries) if entries else stdin_text
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

    def _replace_with_counts(self, text, entries):
        replacements = []
        for entry in entries:
            if not entry.value:
                raise ValueError("Entry value cannot be empty.")
            replacements.append(
                (entry.value, pseudonym_for(entry), entry.category)
            )

        replacements.sort(key=lambda item: (-len(item[0]), item[0], item[1]))

        counts = defaultdict(int)
        output = text
        for value, pseudonym, category in replacements:
            occurrences = output.count(value)
            if not occurrences:
                continue
            counts[category] += occurrences
            output = output.replace(value, pseudonym)

        return output, counts
