import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from iir.cli import main

from .models import Entry
from .replacement import pseudonym_for, replace


class EntryModelTests(TestCase):
    def test_value_unique_within_category(self):
        Entry.objects.create(category="HOST", value="srv-prod-01")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Entry.objects.create(category="HOST", value="srv-prod-01")

        # Same value is allowed in a different category.
        Entry.objects.create(category="SERVICE", value="srv-prod-01")

    def test_pseudonym_requires_saved_entry(self):
        unsaved = Entry(category="HOST", value="unsaved")

        with self.assertRaises(ValueError):
            pseudonym_for(unsaved)


class ReplacementTests(TestCase):
    def test_inactive_entries_are_skipped(self):
        active = Entry.objects.create(category="HOST", value="active-host")
        Entry.objects.create(
            category="HOST", value="offline-host", is_active=False
        )

        result = replace("active-host offline-host")
        self.assertEqual(result, f"Host{active.id} offline-host")

    def test_replacements_apply_longest_value_first(self):
        long_entry = Entry.objects.create(category="HOST", value="srv-prod-01")
        short_entry = Entry.objects.create(category="HOST", value="srv")

        result = replace("srv-prod-01 srv srv-prod-01")

        self.assertEqual(
            result,
            f"Host{long_entry.id} Host{short_entry.id} Host{long_entry.id}",
        )

    def test_multiple_categories_are_replaced(self):
        host = Entry.objects.create(category="HOST", value="alpha")
        service = Entry.objects.create(category="SERVICE", value="bravo")

        result = replace("alpha bravo")

        self.assertEqual(result, f"Host{host.id} Service{service.id}")

    def test_empty_values_raise(self):
        entry = Entry.objects.create(category="WORD", value="")

        with self.assertRaises(ValueError):
            replace("anything", entries=[entry])


class ReplaceViewTests(TestCase):
    def setUp(self):
        self.url = reverse("replace")

    def test_get_sets_default_categories_and_empty_output(self):
        Entry.objects.create(category="HOST", value="alpha")
        Entry.objects.create(category="WORD", value="beta", is_active=False)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context["selected_categories"]),
            {"HOST"},
        )
        self.assertEqual(list(response.context["categories"]), ["HOST"])
        self.assertEqual(response.context["output"], "")
        self.assertEqual(response.context["text"], "")

    def test_post_applies_selected_categories_only(self):
        host = Entry.objects.create(category="HOST", value="alpha")
        Entry.objects.create(category="NAME", value="bravo")
        Entry.objects.create(category="WORD", value="charlie", is_active=False)

        response = self.client.post(
            self.url, {"text": "alpha bravo", "categories": ["HOST"]}
        )

        self.assertContains(response, f"Host{host.id}")
        self.assertContains(response, "bravo")

    def test_get_with_no_entries_renders_without_categories(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["categories"]), [])
        self.assertEqual(set(response.context["selected_categories"]), set())
        self.assertEqual(response.context["output"], "")


class ReplaceTextCommandTests(TestCase):
    def run_command(self, args=None, stdin_value=""):
        args = args or []
        out = StringIO()
        err = StringIO()
        stdin = StringIO(stdin_value)
        with patch("sys.stdin", stdin):
            call_command("replace_text", *args, stdout=out, stderr=err)
        return out.getvalue(), err.getvalue()

    def test_replaces_all_categories_by_default(self):
        host = Entry.objects.create(category="HOST", value="alpha")
        word = Entry.objects.create(category="WORD", value="bravo")

        out, err = self.run_command(stdin_value="alpha bravo")

        self.assertEqual(err, "")
        self.assertEqual(out, f"Host{host.id} Word{word.id}")

    def test_category_filter_limits_replacement(self):
        host = Entry.objects.create(category="HOST", value="alpha")
        Entry.objects.create(category="WORD", value="bravo")

        out, err = self.run_command(args=["--category", "HOST"], stdin_value="alpha bravo")

        self.assertEqual(err, "")
        self.assertEqual(out, f"Host{host.id} bravo")

    def test_exclude_filter_applies_when_no_category_list(self):
        host = Entry.objects.create(category="HOST", value="alpha")
        Entry.objects.create(category="WORD", value="bravo")

        out, err = self.run_command(args=["--exclude", "WORD"], stdin_value="alpha bravo")

        self.assertEqual(err, "")
        self.assertEqual(out, f"Host{host.id} bravo")

    def test_dry_run_reports_counts_and_omits_output(self):
        Entry.objects.create(category="HOST", value="alpha")

        out, err = self.run_command(args=["--dry-run"], stdin_value="alpha alpha")

        self.assertEqual(out, "")
        self.assertEqual(err.strip(), "HOST: 2")


class CliEntryPointTests(TestCase):
    def test_dev_init_creates_secret_file_without_django(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch(
            "iir.cli.SECRET_PATH", Path(tmpdir) / ".env.secret"
        ), patch("iir.cli.django.setup") as setup:
            exit_code = main(["dev-init"])

        self.assertEqual(exit_code, 0)
        self.assertFalse(setup.called)
        secret_file = Path(tmpdir) / ".env.secret"
        self.assertTrue(secret_file.exists())
        content = secret_file.read_text()
        self.assertTrue(content.startswith("DJANGO_SECRET_KEY="))
        self.assertNotEqual(content.strip(), "DJANGO_SECRET_KEY=")

    def test_dev_init_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            secret_file = Path(tmpdir) / ".env.secret"
            secret_file.write_text("DJANGO_SECRET_KEY=existing\n")

            with patch("iir.cli.SECRET_PATH", secret_file):
                exit_code = main(["dev-init"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(secret_file.read_text(), "DJANGO_SECRET_KEY=existing\n")

    def test_unknown_subcommand_exits_with_error(self):
        with patch("sys.stderr", new=StringIO()) as stderr:
            exit_code = main(["unknown"])
        self.assertNotEqual(exit_code, 0)
        self.assertIn("Unknown subcommand", stderr.getvalue())

    def test_replace_subcommand_invokes_management_command(self):
        with patch("iir.cli.call_command") as call_cmd:
            exit_code = main(["replace", "--category", "HOST"])

        self.assertEqual(exit_code, 0)
        call_cmd.assert_called_once_with("replace_text", "--category", "HOST")
