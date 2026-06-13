from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('chat/clear/', views.clear_chat, name='clear_chat'),
    path('messages/', views.inbox, name='inbox'),
    path('messages/new/', views.new_conversation, name='new_conversation'),
    path('messages/<str:username>/delete/', views.delete_conversation, name='delete_conversation'),
    path('messages/<str:username>/', views.conversation, name='conversation'),
    # E2E key endpoints
    path('api/keys/save/', views.save_keys, name='save_keys'),
    path('api/keys/<str:username>/', views.get_public_key, name='get_public_key'),
]
