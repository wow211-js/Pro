from django.contrib import admin

from .models import ChatMessage, VisitorSession


@admin.register(VisitorSession)
class VisitorSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'short_user_agent', 'last_seen', 'first_seen')
    list_filter = ('last_seen', 'first_seen')
    search_fields = ('user__username', 'ip_address', 'user_agent', 'session_key')
    readonly_fields = ('session_key', 'user', 'ip_address', 'user_agent', 'first_seen', 'last_seen')

    def short_user_agent(self, obj):
        return obj.user_agent[:80]

    short_user_agent.short_description = 'Устройство / браузер'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'short_text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'text')
    readonly_fields = ('user', 'text', 'created_at')

    def short_text(self, obj):
        return obj.text[:80]

    short_text.short_description = 'Сообщение'
