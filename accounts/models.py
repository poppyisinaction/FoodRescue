from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('DONOR', 'Food Donor (Restaurant / Hotel / Supermarket / Individual)'),
        ('NGO', 'NGO / Charitable Receiver / Food Bank'),
        ('ADMIN', 'Platform Administrator'),
    ]

    VERIFICATION_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified Organization'),
        ('REJECTED', 'Verification Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='DONOR')
    phone = models.CharField(max_length=25, blank=True)
    organization_name = models.CharField(max_length=180, blank=True)
    organization_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g. Restaurant, Hotel, Supermarket, Orphanage, Shelter, Food Bank"
    )
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True, default='Mumbai')
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default='PENDING')
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['verification_status']),
        ]

    def __str__(self):
        org = f" ({self.organization_name})" if self.organization_name else ""
        return f"{self.user.username} - {self.get_role_display()}{org}"

    @property
    def is_donor(self):
        return self.role == 'DONOR'

    @property
    def is_ngo(self):
        return self.role == 'NGO'

    @property
    def is_platform_admin(self):
        return self.role == 'ADMIN' or self.user.is_superuser

    @property
    def is_verified(self):
        return self.verification_status == 'VERIFIED'


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        role = 'ADMIN' if instance.is_superuser else 'DONOR'
        status = 'VERIFIED' if instance.is_superuser else 'PENDING'
        UserProfile.objects.create(user=instance, role=role, verification_status=status)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
