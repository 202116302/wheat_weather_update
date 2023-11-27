from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing),
    path('2', views.landing2),
    path('buan', views.landing3)
]