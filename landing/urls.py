from django.urls import path
from . import views

urlpatterns = [
    path('iksan', views.landing),
    path('2', views.landing2),
    path('', views.landing3),
    path('daeun', views.landing_d)
]