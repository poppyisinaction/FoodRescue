from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class FoodDonation(models.Model):
    CATEGORY_CHOICES = [
        ('COOKED_MEALS', 'Cooked Meals / Prepared Food'),
        ('BAKERY', 'Bakery & Bread Items'),
        ('PRODUCE', 'Fresh Produce (Fruits & Vegetables)'),
        ('PACKAGED', 'Packaged & Canned Goods'),
        ('DAIRY', 'Dairy Products'),
        ('GRAINS', 'Grains, Rice & Dry Goods'),
        ('BEVERAGES', 'Beverages & Juices'),
        ('OTHER', 'Other Surplus Food'),
    ]

    UNIT_CHOICES = [
        ('kg', 'Kilograms (kg)'),
        ('meals', 'Meals / Plates'),
        ('packets', 'Packets / Boxes'),
        ('liters', 'Liters (L)'),
        ('servings', 'Servings / Portions'),
    ]

    FOOD_TYPE_CHOICES = [
        ('VEG', 'Vegetarian (Pure Veg)'),
        ('NON_VEG', 'Non-Vegetarian'),
        ('VEGAN', '100% Vegan'),
    ]

    STORAGE_CHOICES = [
        ('ROOM_TEMP', 'Room Temperature / Dry Storage'),
        ('REFRIGERATED', 'Refrigerated (0°C to 4°C)'),
        ('FROZEN', 'Frozen (-18°C or below)'),
        ('INSULATED', 'Insulated Hot Container (Above 60°C)'),
    ]

    STATUS_CHOICES = [
        ('AVAILABLE', 'Available for Request'),
        ('ACCEPTED', 'Reserved / Request Accepted'),
        ('COMPLETED', 'Donation Completed & Picked Up'),
        ('CANCELLED', 'Cancelled / Expired'),
    ]

    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations')
    food_name = models.CharField(max_length=200, help_text="e.g. 50 Fresh Vegetable Biryani Packs")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='COOKED_MEALS')
    description = models.TextField(help_text="Detailed ingredients, allergen notice, preparation notes, etc.")
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='meals')
    food_type = models.CharField(max_length=20, choices=FOOD_TYPE_CHOICES, default='VEG')
    
    preparation_datetime = models.DateTimeField(help_text="When was this food cooked or prepared?")
    expiry_datetime = models.DateTimeField(help_text="When must this food be consumed by?")
    
    pickup_location = models.CharField(max_length=255, help_text="Street address, landmark, area")
    pickup_time = models.CharField(max_length=150, help_text="e.g., Today 4:00 PM - 8:00 PM")
    image = models.ImageField(upload_to='donations/', blank=True, null=True)
    
    storage_requirements = models.CharField(max_length=50, choices=STORAGE_CHOICES, default='ROOM_TEMP')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    
    contact_person = models.CharField(max_length=120, blank=True)
    contact_phone = models.CharField(max_length=25, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['food_type']),
            models.Index(fields=['expiry_datetime']),
        ]

    def __str__(self):
        return f"{self.food_name} ({self.quantity} {self.unit}) by {self.donor.username}"

    @property
    def is_available(self):
        return self.status == 'AVAILABLE' and self.expiry_datetime > timezone.now()

    @property
    def is_expired(self):
        return self.expiry_datetime <= timezone.now()

    @property
    def hours_until_expiry(self):
        diff = self.expiry_datetime - timezone.now()
        return round(diff.total_seconds() / 3600, 1)


class DonationHistory(models.Model):
    donation = models.ForeignKey(FoodDonation, on_delete=models.CASCADE, related_name='history_records')
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations_made_history')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations_received_history')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    completed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Feedback or confirmation notes upon pickup")

    class Meta:
        ordering = ['-completed_at']
        verbose_name_plural = "Donation Histories"

    def __str__(self):
        return f"{self.donation.food_name} transferred from {self.donor.username} to {self.receiver.username}"
