from django.urls import path

from . import views
from .views import CustomLoginView

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('chat/clear/', views.clear_chat, name='clear_chat'),
    path('2fa/setup/', views.totp_setup, name='totp_setup'),
    path('2fa/verify/', views.totp_verify, name='totp_verify'),
    path('messages/', views.inbox, name='inbox'),
    path('messages/new/', views.new_conversation, name='new_conversation'),
    path('messages/<str:username>/delete/', views.delete_conversation, name='delete_conversation'),
    path('messages/<str:username>/block/', views.block_user, name='block_user'),
    path('messages/<str:username>/unblock/', views.unblock_user, name='unblock_user'),
    path('messages/<str:username>/', views.conversation, name='conversation'),
    # E2E key endpoints
    path('api/keys/save/', views.save_keys, name='save_keys'),
    path('api/messages/<str:username>/poll/', views.poll_messages, name='poll_messages'),
    path('api/keys/<str:username>/', views.get_public_key, name='get_public_key'),
    path('api/chat/poll/', views.poll_chat, name='poll_chat'),
]
