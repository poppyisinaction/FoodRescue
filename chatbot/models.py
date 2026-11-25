from django.db import models
from django.contrib.auth.models import User


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_messages')
    session_id = models.CharField(max_length=100, blank=True, help_text="Session identifier for anonymous visitors")
    message = models.TextField()
    response = models.TextField()
    used_llm = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        user_str = self.user.username if self.user else f"Guest ({self.session_id[:8]})"
        return f"Chat by {user_str} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
