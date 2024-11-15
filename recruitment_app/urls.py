from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('login',views.login_view,name='.login_view'),
    path('candidate',views.candidate,name='candidate'),
    path('interviewer',views.interviewer,name='interviewer'),
    path('addJob',views.addJob,name='addJob'),
    path('register',views.register,name='register'),
    path('logout', views.logout_view, name='logout'),
    path('interviewerinfo',views.interviewer_info,name='interviewer_info'),
    path('update_info',views.update_info,name='UpdateInfo'),
    path('scheduled_interview',views.scheduled_interview,name='scheduled_interview'),
    path('add_job',views.add_job,name='add_job'),
    path('apply',views.submit_application, name='submit_application'),
]

