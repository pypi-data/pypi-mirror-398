from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from dictionary.models import Entry
from dictionary.replacement import replace


class AuthenticatedAPITestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester", password="password"
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")


class ReplaceAPITests(AuthenticatedAPITestCase):
    def test_requires_authentication(self):
        anon_client = APIClient()
        response = anon_client.post("/api/v1/replace", {"text": "alpha"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_replacement_uses_existing_logic_longest_first(self):
        long_entry = Entry.objects.create(category="HOST", value="srv-prod-01")
        short_entry = Entry.objects.create(category="HOST", value="srv")

        response = self.client.post(
            "/api/v1/replace",
            {"text": "srv-prod-01 srv", "include_categories": ["HOST"]},
            format="json",
        )

        expected = replace(
            "srv-prod-01 srv", entries=Entry.objects.filter(category="HOST")
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"text": expected})
        self.assertIn(f"Host{long_entry.id}", response.data["text"])
        self.assertIn(f"Host{short_entry.id}", response.data["text"])

    def test_category_exclusion(self):
        host_entry = Entry.objects.create(category="HOST", value="alpha")
        Entry.objects.create(category="WORD", value="beta")

        response = self.client.post(
            "/api/v1/replace",
            {"text": "alpha beta", "exclude_categories": ["WORD"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"text": f"Host{host_entry.id} beta"})


class CategoriesAPITests(AuthenticatedAPITestCase):
    def test_requires_authentication(self):
        anon_client = APIClient()
        response = anon_client.get("/api/v1/categories")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_distinct_active_categories(self):
        Entry.objects.create(category="HOST", value="alpha")
        Entry.objects.create(category="HOST", value="beta")
        Entry.objects.create(category="SERVICE", value="gamma", is_active=False)
        Entry.objects.create(category="DOMAIN", value="delta")

        response = self.client.get("/api/v1/categories")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data["categories"]), {"HOST", "DOMAIN"})


class HealthEndpointTests(TestCase):
    def test_health_endpoints_do_not_require_auth(self):
        client = APIClient()
        for path in ["/health/startup/", "/health/live/", "/health/ready/"]:
            response = client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ready_checks_database_connectivity(self):
        client = APIClient()
        Entry.objects.create(category="HOST", value="alpha")
        response = client.get("/health/ready/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok"})
