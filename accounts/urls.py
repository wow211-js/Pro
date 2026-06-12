from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('devices/', views.devices, name='devices'),
    path('chat/clear/', views.clear_chat, name='clear_chat'),
]
