from django.test import TestCase, Client
from django.urls import reverse
from wagtail.test.utils import WagtailPageTests
from wagtail.models import Page

from .models import ExamplePage


class {{app_class_name}}ViewTests(TestCase):
    """Test views for {{app_name}} app."""
    
    def setUp(self):
        self.client = Client()
    
    def test_index_view(self):
        """Test the index view."""
        response = self.client.get(reverse('{{app_name}}:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hello from {{app_name}}')
    
    def test_example_view(self):
        """Test the example view."""
        response = self.client.get(reverse('{{app_name}}:example'))
        self.assertEqual(response.status_code, 200)


class ExamplePageTests(WagtailPageTests):
    """Test ExamplePage model."""
    
    def test_can_create_example_page(self):
        """Test that we can create an ExamplePage."""
        # Get the root page (adjust if your root ID differs)
        root_page = Page.objects.first()
        
        # Create an ExamplePage
        example_page = ExamplePage(
            title="Test Example Page",
            introduction="This is a test page",
            slug="test-example-page"
        )
        
        # Add it as a child of the root page
        root_page.add_child(instance=example_page)
        
        # Check that the page was created
        self.assertTrue(ExamplePage.objects.filter(title="Test Example Page").exists())
    
    def test_example_page_str(self):
        """Test the string representation of ExamplePage."""
        page = ExamplePage(title="Test Page")
        self.assertEqual(str(page), "Test Page")
