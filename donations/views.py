from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import FoodDonation, DonationHistory
from .forms import FoodDonationForm
from notifications.models import Notification


def available_donations_view(request):
    """
    Publicly browsable listing of all currently active and unexpired food donations.
    Provides multi-parameter search, category filter, dietary filter, and sorting.
    """
    now = timezone.now()
    donations = FoodDonation.objects.filter(status='AVAILABLE', expiry_datetime__gt=now)
    
    # Search Query
    q = request.GET.get('q', '').strip()
    if q:
        donations = donations.filter(
            Q(food_name__icontains=q) |
            Q(description__icontains=q) |
            Q(pickup_location__icontains=q) |
            Q(donor__username__icontains=q) |
            Q(donor__profile__organization_name__icontains=q)
        )

    # Category Filter
    category = request.GET.get('category', '').strip()
    if category:
        donations = donations.filter(category=category)

    # Food Type Filter (Veg/Non-Veg/Vegan)
    food_type = request.GET.get('food_type', '').strip()
    if food_type:
        donations = donations.filter(food_type=food_type)

    # City / Location Filter
    location = request.GET.get('location', '').strip()
    if location:
        donations = donations.filter(pickup_location__icontains=location)

    # Sorting
    sort = request.GET.get('sort', 'latest')
    if sort == 'expiring':
        donations = donations.order_by('expiry_datetime')
    elif sort == 'quantity':
        donations = donations.order_by('-quantity')
    else:
        donations = donations.order_by('-created_at')

    categories = FoodDonation.CATEGORY_CHOICES
    food_types = FoodDonation.FOOD_TYPE_CHOICES

    context = {
        'donations': donations,
        'total_count': donations.count(),
        'categories': categories,
        'food_types': food_types,
        'selected_category': category,
        'selected_food_type': food_type,
        'selected_location': location,
        'selected_sort': sort,
        'search_query': q,
    }
    return render(request, 'donations/available_donations.html', context)


@login_required
def add_donation_view(request):
    """
    Enables registered food donors (or administrators) to create a new surplus food donation.
    """
    if not (request.user.profile.is_donor or request.user.is_superuser or request.user.profile.is_platform_admin):
        messages.warning(request, "Only registered Food Donors can post food surplus. Please switch to a Donor account.")
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = FoodDonationForm(request.POST, request.FILES)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.donor = request.user
            donation.status = 'AVAILABLE'
            donation.save()

            # Create notification for donor
            Notification.objects.create(
                recipient=request.user,
                title="Donation Created Successfully",
                message=f"Your donation listing for '{donation.food_name}' ({donation.quantity} {donation.unit}) is now live for NGOs.",
                notification_type='STATUS',
                link=f"/donations/{donation.id}/"
            )

            messages.success(request, f"Your surplus food '{donation.food_name}' has been listed successfully!")
            return redirect('donor_dashboard')
        else:
            messages.error(request, "Please check the form inputs. Expiry must be later than preparation time.")
    else:
        initial = {
            'pickup_location': request.user.profile.address or '',
            'contact_person': request.user.get_full_name() or request.user.username,
            'contact_phone': request.user.profile.phone or '',
            'preparation_datetime': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'expiry_datetime': (timezone.now() + timezone.timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M'),
        }
        form = FoodDonationForm(initial=initial)

    return render(request, 'donations/add_donation.html', {'form': form})


def donation_detail_view(request, donation_id):
    """
    Detailed view for an individual food donation.
    Shows specifications, donor details, countdown timer, and claim status.
    """
    donation = get_object_or_404(FoodDonation, id=donation_id)
    
    # Check if this user is an NGO who already requested this food
    user_request = None
    if request.user.is_authenticated and request.user.profile.is_ngo:
        user_request = donation.requests.filter(ngo=request.user).first()

    # All requests for donor view
    all_requests = donation.requests.all() if (request.user == donation.donor or request.user.is_superuser) else []

    context = {
        'donation': donation,
        'user_request': user_request,
        'all_requests': all_requests,
        'is_owner': request.user == donation.donor or request.user.is_superuser,
    }
    return render(request, 'donations/donation_detail.html', context)


@login_required
def edit_donation_view(request, donation_id):
    """
    Allows the donor to edit their listing if it has not yet been accepted.
    """
    donation = get_object_or_404(FoodDonation, id=donation_id)
    if donation.donor != request.user and not request.user.is_superuser:
        messages.error(request, "You are not authorized to edit this donation.")
        return redirect('available_donations')

    if donation.status != 'AVAILABLE':
        messages.warning(request, "Cannot edit a donation that has already been accepted or completed.")
        return redirect('donation_detail', donation_id=donation.id)

    if request.method == 'POST':
        form = FoodDonationForm(request.POST, request.FILES, instance=donation)
        if form.is_valid():
            form.save()
            messages.success(request, "Donation details updated successfully.")
            return redirect('donation_detail', donation_id=donation.id)
    else:
        form = FoodDonationForm(instance=donation)

    return render(request, 'donations/edit_donation.html', {'form': form, 'donation': donation})


@login_required
def cancel_donation_view(request, donation_id):
    """
    Allows donor to cancel their donation.
    """
    donation = get_object_or_404(FoodDonation, id=donation_id)
    if donation.donor != request.user and not request.user.is_superuser:
        messages.error(request, "You are not authorized to modify this donation.")
        return redirect('available_donations')

    donation.status = 'CANCELLED'
    donation.save()
    
    # Reject any pending requests with notification
    for req in donation.requests.filter(status='PENDING'):
        req.status = 'CANCELLED'
        req.donor_response_message = "Donation listing was cancelled by donor."
        req.save()
        Notification.objects.create(
            recipient=req.ngo,
            title="Food Request Cancelled",
            message=f"The donation for '{donation.food_name}' was cancelled by the donor.",
            notification_type='CANCEL',
            link="/dashboard/ngo/"
        )

    messages.info(request, "Donation listing has been cancelled.")
    return redirect('donor_dashboard')


@login_required
def donation_history_view(request):
    """
    Displays platform-wide or user-specific history of completed food rescues.
    """
    if request.user.is_superuser or request.user.profile.is_platform_admin:
        history_records = DonationHistory.objects.all()
    elif request.user.profile.is_donor:
        history_records = DonationHistory.objects.filter(donor=request.user)
    elif request.user.profile.is_ngo:
        history_records = DonationHistory.objects.filter(receiver=request.user)
    else:
        history_records = DonationHistory.objects.none()

    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        history_records = history_records.filter(
            Q(donation__food_name__icontains=q) |
            Q(donor__username__icontains=q) |
            Q(receiver__username__icontains=q) |
            Q(notes__icontains=q)
        )

    context = {
        'history_records': history_records,
        'search_query': q,
    }
    return render(request, 'donations/donation_history.html', context)
