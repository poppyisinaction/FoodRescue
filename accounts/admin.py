from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'organization_name', 'city', 'phone', 'verification_status', 'created_at')
    list_filter = ('role', 'verification_status', 'city')
    search_fields = ('user__username', 'user__email', 'organization_name', 'phone')
    actions = ['mark_verified', 'mark_pending']

    @admin.action(description="Mark selected users as Verified")
    def mark_verified(self, request, queryset):
        queryset.update(verification_status='VERIFIED')

    @admin.action(description="Mark selected users as Pending Verification")
    def mark_pending(self, request, queryset):
        queryset.update(verification_status='PENDING')
