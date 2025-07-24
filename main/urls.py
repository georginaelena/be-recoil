from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_endpoint, name='test_endpoint'),
]
