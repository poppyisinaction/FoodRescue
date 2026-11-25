from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('REQUEST', 'New Food Request'),
        ('ACCEPT', 'Request Accepted'),
        ('REJECT', 'Request Rejected'),
        ('CANCEL', 'Donation / Request Cancelled'),
        ('COMPLETE', 'Donation Completed'),
        ('STATUS', 'Status Update'),
        ('SYSTEM', 'System Announcement'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, help_text="Destination dashboard URL")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='SYSTEM')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
        ]

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"
