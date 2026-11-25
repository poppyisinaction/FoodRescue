from django.contrib import admin
from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_id', 'message_snippet', 'used_llm', 'created_at')
    list_filter = ('used_llm', 'created_at')
    search_fields = ('message', 'response', 'user__username')

    def message_snippet(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_snippet.short_description = "User Message"
