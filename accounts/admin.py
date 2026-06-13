from django.contrib import admin

from .models import ChatMessage, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name')
    search_fields = ('user__username', 'display_name')
    readonly_fields = ('user',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'short_text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'text')
    readonly_fields = ('user', 'text', 'created_at')

    def short_text(self, obj):
        return obj.text[:80]

    short_text.short_description = 'Сообщение'
