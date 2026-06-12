from django.contrib import admin

from .models import ChatMessage, VisitorSession


@admin.register(VisitorSession)
class VisitorSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_hash', 'last_seen', 'first_seen')
    list_filter = ('last_seen', 'first_seen')
    search_fields = ('user__username', 'session_key')
    readonly_fields = ('session_key', 'user', 'ip_hash', 'first_seen', 'last_seen')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'short_text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'text')
    readonly_fields = ('user', 'text', 'created_at')

    def short_text(self, obj):
        return obj.text[:80]

    short_text.short_description = 'Сообщение'
