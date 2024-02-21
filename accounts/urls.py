from django.urls import path
from django.contrib.auth.views import LoginView
from . import views

urlpatterns = [
    path('',views.index, name='index'),
    path('about/', views.about, name='about'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),

]