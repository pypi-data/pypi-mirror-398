from django.urls import path
from . import views

app_name = '{{app_name}}'

urlpatterns = [
    path('', views.index, name='index'),
    path('example/', views.example_view, name='example'),
]
