"""
URL configuration for foodrescue project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views
from donations import views as donation_views

urlpatterns = [
    # Platform Core Admin
    path('admin/', admin.site.urls),

    # Direct convenient shortcuts
    path('login/', account_views.login_view, name='login'),
    path('register/', account_views.register_view, name='register'),
    path('logout/', account_views.logout_view, name='logout'),
    path('profile/', account_views.profile_view, name='profile'),
    path('available-food/', donation_views.available_donations_view, name='available_donations'),
    path('donate-food/', donation_views.add_donation_view, name='add_donation'),
    path('donation-history/', donation_views.donation_history_view, name='donation_history'),

    # Modular Apps
    path('accounts/', include('accounts.urls')),
    path('donations/', include('donations.urls')),
    path('requests/', include('food_requests.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('notifications/', include('notifications.urls')),
    path('', include('core.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom Admin Site Branding
admin.site.site_header = "FoodRescue Platform Administration"
admin.site.site_title = "FoodRescue Admin Portal"
admin.site.index_title = "Welcome to FoodRescue Operations & Control Center"
