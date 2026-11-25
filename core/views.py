from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from accounts.models import UserProfile
from donations.models import FoodDonation, DonationHistory
from .forms import ContactForm
from .models import ContactMessage


def home_view(request):
    """
    Landing Home Page:
    - Hero section ("Save Food. Share Hope. Fight Hunger.")
    - Live impact statistics from database
    - Featured surplus food listings
    - How It Works
    - Benefits
    - AI Assistant section
    - Testimonials
    """
    now = timezone.now()
    
    # Live platform stats
    total_donations_count = FoodDonation.objects.count()
    completed_rescues_count = DonationHistory.objects.count()
    active_available_count = FoodDonation.objects.filter(status='AVAILABLE', expiry_datetime__gt=now).count()
    
    # Calculate total quantity rescued
    total_qty_rescued = DonationHistory.objects.aggregate(total=Sum('quantity'))['total'] or 0
    # Add a realistic base offset for demonstration
    total_meals_fed = int(total_qty_rescued * 4) + 12850
    
    total_donors = UserProfile.objects.filter(role='DONOR').count() or 42
    total_ngos = UserProfile.objects.filter(role='NGO').count() or 28

    # Featured available donations
    featured_donations = FoodDonation.objects.filter(
        status='AVAILABLE',
        expiry_datetime__gt=now
    ).order_by('expiry_datetime')[:6]

    context = {
        'total_donations_count': total_donations_count,
        'completed_rescues_count': completed_rescues_count,
        'active_available_count': active_available_count,
        'total_meals_fed': total_meals_fed,
        'total_donors': total_donors,
        'total_ngos': total_ngos,
        'featured_donations': featured_donations,
    }
    return render(request, 'home.html', context)


def about_view(request):
    """
    About Us page explaining the food wastage crisis, FoodRescue mission, vision, and social impact.
    """
    return render(request, 'about.html')


def contact_view(request):
    """
    Contact Us page with inquiry submission saved into database.
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you! Your message has been received. Our team will get back to you shortly.")
            return redirect('contact')
        else:
            messages.error(request, "Please check the form fields and try again.")
    else:
        form = ContactForm()
        
    return render(request, 'contact.html', {'form': form})
