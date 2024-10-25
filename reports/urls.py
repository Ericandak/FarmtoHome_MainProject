from django.urls import path
from . import views

urlpatterns = [
path('generate/', views.generate_sales_report, name='generate_sales_report'),
]