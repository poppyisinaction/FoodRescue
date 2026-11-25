from django.contrib import admin
from .models import FoodRequest


@admin.register(FoodRequest)
class FoodRequestAdmin(admin.ModelAdmin):
    list_display = ('donation', 'ngo', 'status', 'estimated_pickup_time', 'requested_at')
    list_filter = ('status', 'requested_at')
    search_fields = ('donation__food_name', 'ngo__username', 'request_message')
