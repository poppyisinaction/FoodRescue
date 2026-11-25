from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum
import json
from accounts.models import UserProfile
from donations.models import FoodDonation, DonationHistory
from food_requests.models import FoodRequest
from core.models import ContactMessage


@login_required
def donor_dashboard_view(request):
    """
    Donor Dashboard displaying live statistics, chart metrics, and recent donation activity.
    """
    if not (request.user.profile.is_donor or request.user.is_superuser):
        return redirect('dashboard_redirect')

    user = request.user
    my_donations = FoodDonation.objects.filter(donor=user)

    total_donations = my_donations.count()
    available_donations = my_donations.filter(status='AVAILABLE').count()
    accepted_donations = my_donations.filter(status='ACCEPTED').count()
    completed_donations = my_donations.filter(status='COMPLETED').count()

    # Incoming requests across all this donor's donations
    incoming_requests = FoodRequest.objects.filter(donation__donor=user).select_related('donation', 'ngo').order_by('-requested_at')[:10]
    pending_requests_count = FoodRequest.objects.filter(donation__donor=user, status='PENDING').count()

    # Category breakdown for Chart.js
    category_counts = my_donations.values('category').annotate(count=Count('id'))
    cat_labels = [c['category'] for c in category_counts]
    cat_data = [c['count'] for c in category_counts]

    # Status breakdown
    status_data = {
        'Available': available_donations,
        'Accepted': accepted_donations,
        'Completed': completed_donations,
        'Cancelled': my_donations.filter(status='CANCELLED').count()
    }

    context = {
        'total_donations': total_donations,
        'available_donations': available_donations,
        'accepted_donations': accepted_donations,
        'completed_donations': completed_donations,
        'pending_requests_count': pending_requests_count,
        'recent_donations': my_donations[:8],
        'incoming_requests': incoming_requests,
        'chart_categories_json': json.dumps(cat_labels),
        'chart_cat_counts_json': json.dumps(cat_data),
        'chart_status_json': json.dumps(status_data),
    }
    return render(request, 'dashboard/donor_dashboard.html', context)


@login_required
def ngo_dashboard_view(request):
    """
    NGO Dashboard showing available donations, claim requests, completed pickups, and tracking.
    """
    if not (request.user.profile.is_ngo or request.user.is_superuser):
        return redirect('dashboard_redirect')

    user = request.user
    my_requests = FoodRequest.objects.filter(ngo=user).select_related('donation', 'donation__donor').order_by('-requested_at')

    pending_requests = my_requests.filter(status='PENDING').count()
    accepted_requests = my_requests.filter(status='ACCEPTED').count()
    completed_pickups = my_requests.filter(status='COMPLETED').count()
    
    # Available donations in the platform
    available_donations = FoodDonation.objects.filter(status='AVAILABLE', expiry_datetime__gt=timezone.now())
    total_available_food = available_donations.count()

    # Recent available food recommendations
    recommended_food = available_donations.order_by('expiry_datetime')[:6]

    context = {
        'total_available_food': total_available_food,
        'pending_requests': pending_requests,
        'accepted_requests': accepted_requests,
        'completed_pickups': completed_pickups,
        'my_requests': my_requests[:10],
        'recommended_food': recommended_food,
    }
    return render(request, 'dashboard/ngo_dashboard.html', context)


@login_required
def admin_dashboard_view(request):
    """
    Custom Platform Administrator Dashboard:
    - User management (verify NGO/Donor, activate/deactivate account)
    - Donation oversight
    - Request tracking
    - Platform analytics
    """
    if not (request.user.is_superuser or request.user.profile.is_platform_admin):
        messages.error(request, "Access restricted to Platform Administrators.")
        return redirect('home')

    total_users = User.objects.count()
    total_donors = UserProfile.objects.filter(role='DONOR').count()
    total_ngos = UserProfile.objects.filter(role='NGO').count()
    pending_verifications = UserProfile.objects.filter(verification_status='PENDING').count()

    total_donations = FoodDonation.objects.count()
    available_donations = FoodDonation.objects.filter(status='AVAILABLE').count()
    accepted_donations = FoodDonation.objects.filter(status='ACCEPTED').count()
    completed_donations = FoodDonation.objects.filter(status='COMPLETED').count()
    cancelled_donations = FoodDonation.objects.filter(status='CANCELLED').count()

    total_requests = FoodRequest.objects.count()
    pending_requests = FoodRequest.objects.filter(status='PENDING').count()

    # Inquiries
    unresolved_inquiries = ContactMessage.objects.filter(is_resolved=False).count()
    recent_inquiries = ContactMessage.objects.all().order_by('-created_at')[:5]

    # Recent users
    recent_users = User.objects.select_related('profile').order_by('-date_joined')[:10]
    recent_donations = FoodDonation.objects.select_related('donor').order_by('-created_at')[:8]

    # Chart data
    analytics_labels = ['Available', 'In Progress / Accepted', 'Completed', 'Cancelled']
    analytics_counts = [available_donations, accepted_donations, completed_donations, cancelled_donations]

    context = {
        'total_users': total_users,
        'total_donors': total_donors,
        'total_ngos': total_ngos,
        'pending_verifications': pending_verifications,
        'total_donations': total_donations,
        'available_donations': available_donations,
        'accepted_donations': accepted_donations,
        'completed_donations': completed_donations,
        'cancelled_donations': cancelled_donations,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'unresolved_inquiries': unresolved_inquiries,
        'recent_inquiries': recent_inquiries,
        'recent_users': recent_users,
        'recent_donations': recent_donations,
        'chart_labels_json': json.dumps(analytics_labels),
        'chart_counts_json': json.dumps(analytics_counts),
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def admin_toggle_verification(request, user_id):
    """
    Action for administrators to verify or revoke verification for a user.
    """
    if not (request.user.is_superuser or request.user.profile.is_platform_admin):
        messages.error(request, "Unauthorized action.")
        return redirect('home')

    target_user = get_object_or_404(User, id=user_id)
    profile = target_user.profile
    
    if profile.verification_status == 'VERIFIED':
        profile.verification_status = 'PENDING'
        messages.info(request, f"Verification revoked for {target_user.username}.")
    else:
        profile.verification_status = 'VERIFIED'
        messages.success(request, f"Account for {target_user.username} has been VERIFIED!")
    profile.save()

    return redirect('admin_dashboard')


@login_required
def admin_toggle_active(request, user_id):
    """
    Action for administrators to activate or deactivate a user account.
    """
    if not (request.user.is_superuser or request.user.profile.is_platform_admin):
        messages.error(request, "Unauthorized action.")
        return redirect('home')

    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.warning(request, "You cannot deactivate your own administrative account.")
        return redirect('admin_dashboard')

    target_user.is_active = not target_user.is_active
    target_user.save()
    status_str = "activated" if target_user.is_active else "deactivated"
    messages.info(request, f"User {target_user.username} has been {status_str}.")

    return redirect('admin_dashboard')
