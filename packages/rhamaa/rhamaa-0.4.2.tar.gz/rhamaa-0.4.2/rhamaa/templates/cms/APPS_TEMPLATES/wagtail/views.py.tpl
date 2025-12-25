from django.shortcuts import render
from django.http import HttpResponse
from wagtail.models import Page


# Create your views here.

def index(request):
    """Example view function."""
    return HttpResponse("Hello from {{app_name}} app!")


def example_view(request):
    """Example view with template rendering."""
    context = {
        'app_name': '{{app_name}}',
        'title': '{{app_title}}'
    }
    return render(request, '{{app_name}}/index.html', context)
