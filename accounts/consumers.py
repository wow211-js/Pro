import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from accounts.models import DirectMessage

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.partner_username = self.scope['url_route']['kwargs']['username']
        self.room_name = f'call_{min(self.user.username, self.partner_username)}_{max(self.user.username, self.partner_username)}'
        self.room_group_name = f'call_{self.room_name}'

        # Reject anonymous users
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Broadcast signal to the other peer in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'signal',
                'sender': self.user.username,
                'signal': data,
            }
        )

    async def signal(self, event):
        # Don't send back to the sender
        if event['sender'] != self.user.username:
            await self.send(text_data=json.dumps(event['signal']))
