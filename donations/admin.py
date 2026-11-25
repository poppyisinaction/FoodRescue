from django.contrib import admin
from .models import FoodDonation, DonationHistory


@admin.register(FoodDonation)
class FoodDonationAdmin(admin.ModelAdmin):
    list_display = ('food_name', 'donor', 'category', 'food_type', 'quantity', 'unit', 'status', 'expiry_datetime', 'created_at')
    list_filter = ('status', 'category', 'food_type', 'storage_requirements')
    search_fields = ('food_name', 'description', 'donor__username', 'pickup_location')
    date_hierarchy = 'created_at'


@admin.register(DonationHistory)
class DonationHistoryAdmin(admin.ModelAdmin):
    list_display = ('donation', 'donor', 'receiver', 'quantity', 'unit', 'completed_at')
    list_filter = ('completed_at', 'unit')
    search_fields = ('donation__food_name', 'donor__username', 'receiver__username', 'notes')
