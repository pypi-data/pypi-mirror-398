from django.contrib import admin
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import ExamplePage


# Register your models here.

@admin.register(ExamplePage)
class ExamplePageAdmin(admin.ModelAdmin):
    list_display = ['title', 'live', 'first_published_at']
    list_filter = ['live', 'first_published_at']
    search_fields = ['title', 'introduction']

# Wagtail ModelAdmin (optional)
# class ExampleModelAdmin(ModelAdmin):
#     model = ExamplePage
#     menu_label = 'Example Pages'
#     menu_icon = 'doc-full'
#     list_display = ('title', 'live', 'first_published_at')
#     search_fields = ('title', 'introduction')

# modeladmin_register(ExampleModelAdmin)
