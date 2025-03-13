"""
URL configuration for FarmToHomeProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path,include
from . import views

app_name = 'Delivery'
urlpatterns = [
    path('jobs/', views.jobs, name='jobs'),
    path('apply_job/', views.apply_job, name='apply_job'),
    path('job_requests/', views.job_requests, name='job_requests'),
    path('deliverindex/', views.deliverindex, name='deliverindex'),
    path('start_delivery/<int:order_id>/', views.start_delivery, name='start_delivery'),
    path('complete_delivery/<int:order_id>/', views.complete_delivery, name='complete_delivery'),
    path('fail_delivery/<int:delivery_id>/', views.fail_delivery, name='fail_delivery'),
    path('order_history/', views.order_history, name='order_history'),
    path('update-pincodes/', views.update_delivery_pincodes, name='update_pincodes'),
    path('update_location/',views.update_location,name="update_location")
]
