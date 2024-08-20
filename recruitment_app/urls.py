from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('candidate',views.candidate,name='candidate'),
    path('interviewer',views.interviewer,name='interviewer')
]