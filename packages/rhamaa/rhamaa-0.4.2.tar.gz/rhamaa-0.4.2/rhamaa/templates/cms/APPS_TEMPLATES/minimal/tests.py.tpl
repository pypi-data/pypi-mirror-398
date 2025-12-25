from django.test import TestCase, Client
from django.urls import reverse


class {{app_class_name}}ViewTests(TestCase):
    """Basic tests for {{app_name}} app (minimal template)."""

    def setUp(self):
        self.client = Client()

    def test_index_view(self):
        response = self.client.get(reverse('{{app_name}}:index'))
        self.assertEqual(response.status_code, 200)
