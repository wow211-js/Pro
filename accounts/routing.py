from django.urls import re_path
from accounts import consumers

websocket_urlpatterns = [
    re_path(r'^ws/call/(?P<username>\w+)/$', consumers.CallConsumer.as_asgi()),
]
