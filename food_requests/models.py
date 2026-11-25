from django.db import models
from django.contrib.auth.models import User
from donations.models import FoodDonation


class FoodRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Donor Review'),
        ('ACCEPTED', 'Accepted & Assigned'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed & Collected'),
        ('CANCELLED', 'Cancelled by NGO'),
    ]

    donation = models.ForeignKey(FoodDonation, on_delete=models.CASCADE, related_name='requests')
    ngo = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_requests')
    request_message = models.TextField(
        help_text="State how this food will be distributed, expected beneficiaries, and pickup timeline."
    )
    estimated_pickup_time = models.CharField(
        max_length=150,
        blank=True,
        help_text="Planned pickup window, e.g. Today by 5:30 PM"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    donor_response_message = models.TextField(blank=True, help_text="Note or instructions from the food donor")
    
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-requested_at']
        unique_together = ('donation', 'ngo')  # Prevent duplicate requests from same NGO
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['requested_at']),
        ]

    def __str__(self):
        return f"Request by {self.ngo.username} for {self.donation.food_name} [{self.get_status_display()}]"
