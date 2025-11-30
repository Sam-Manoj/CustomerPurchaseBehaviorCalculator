from django.urls import path
from . import views

urlpatterns = [
    path('calculation/', views.calculation_page, name='calculation'),
]
