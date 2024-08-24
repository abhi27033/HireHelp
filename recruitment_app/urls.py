from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login',views.login_view,name='.login_view'),
    path('candidate',views.candidate,name='candidate'),
    path('interviewer',views.interviewer,name='interviewer'),
    path('register',views.register,name='register'),
<<<<<<< HEAD
    path('logout',views.logout_view,name='logout')
=======
    path('logout', views.logout_view, name='logout')
>>>>>>> e4d4b29cd507a438e85104fe5b8df2a3767c6237
]