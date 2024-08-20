from django.urls import path
from . import views

urlpatterns = [
    path('', views.recruitment_app, name='recruitment_app'),
]