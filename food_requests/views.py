from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from donations.models import FoodDonation, DonationHistory
from notifications.models import Notification
from .models import FoodRequest


@login_required
def create_request_view(request, donation_id):
    """
    Allows a verified or registered NGO to submit a claim request for an available food donation.
    """
    if not (request.user.profile.is_ngo or request.user.is_superuser):
        messages.error(request, "Only registered NGOs and Charitable Receivers can request surplus food.")
        return redirect('donation_detail', donation_id=donation_id)

    donation = get_object_or_404(FoodDonation, id=donation_id)

    if donation.status != 'AVAILABLE':
        messages.warning(request, "This food donation is no longer available.")
        return redirect('donation_detail', donation_id=donation_id)

    if donation.expiry_datetime <= timezone.now():
        messages.warning(request, "This food donation has expired and cannot be requested.")
        return redirect('donation_detail', donation_id=donation_id)

    # Check if NGO already requested
    existing = FoodRequest.objects.filter(donation=donation, ngo=request.user).first()
    if existing:
        messages.info(request, f"You have already requested this food. Status: {existing.get_status_display()}")
        return redirect('donation_detail', donation_id=donation_id)

    if request.method == 'POST':
        message = request.POST.get('request_message', '').strip()
        pickup_time = request.POST.get('estimated_pickup_time', '').strip()

        if not message:
            messages.error(request, "Please provide a request message stating your distribution plan.")
            return redirect('donation_detail', donation_id=donation_id)

        food_req = FoodRequest.objects.create(
            donation=donation,
            ngo=request.user,
            request_message=message,
            estimated_pickup_time=pickup_time,
            status='PENDING'
        )

        # Notify donor
        Notification.objects.create(
            recipient=donation.donor,
            title="New Food Request Received",
            message=f"{request.user.profile.organization_name or request.user.username} has requested your donation: '{donation.food_name}'.",
            notification_type='REQUEST',
            link=f"/donations/{donation.id}/"
        )

        messages.success(request, f"Your request for '{donation.food_name}' has been submitted to the donor!")
        return redirect('ngo_dashboard')

    return render(request, 'requests/request_form.html', {'donation': donation})


@login_required
def accept_request_view(request, request_id):
    """
    Allows the donor to accept an NGO's food request.
    Uses atomic transaction to prevent race conditions and automatically
    marks the donation as ACCEPTED and rejects other competing requests.
    """
    food_request = get_object_or_404(FoodRequest, id=request_id)
    donation = food_request.donation

    if donation.donor != request.user and not request.user.is_superuser:
        messages.error(request, "Unauthorized action.")
        return redirect('donor_dashboard')

    if donation.status != 'AVAILABLE':
        messages.warning(request, "This donation is no longer available.")
        return redirect('donation_detail', donation_id=donation.id)

    with transaction.atomic():
        # Update accepted request
        food_request.status = 'ACCEPTED'
        donor_note = request.POST.get('donor_response_message', '').strip()
        if donor_note:
            food_request.donor_response_message = donor_note
        food_request.save()

        # Update donation status
        donation.status = 'ACCEPTED'
        donation.save()

        # Auto-reject any other pending requests for this same donation
        competing_requests = FoodRequest.objects.filter(donation=donation, status='PENDING').exclude(id=food_request.id)
        for comp in competing_requests:
            comp.status = 'REJECTED'
            comp.donor_response_message = "Donation assigned to another NGO."
            comp.save()

            Notification.objects.create(
                recipient=comp.ngo,
                title="Food Request Status Update",
                message=f"Your request for '{donation.food_name}' was not selected as another organization was assigned.",
                notification_type='REJECT',
                link="/dashboard/ngo/"
            )

        # Notify the accepted NGO
        Notification.objects.create(
            recipient=food_request.ngo,
            title="Request Accepted!",
            message=f"Great news! Your request for '{donation.food_name}' was accepted by {donation.donor.profile.organization_name or donation.donor.username}. Please coordinate pickup.",
            notification_type='ACCEPT',
            link="/dashboard/ngo/"
        )

    messages.success(request, f"You accepted the request from {food_request.ngo.profile.organization_name or food_request.ngo.username}!")
    return redirect('donation_detail', donation_id=donation.id)


@login_required
def reject_request_view(request, request_id):
    """
    Allows donor to reject a specific request.
    """
    food_request = get_object_or_404(FoodRequest, id=request_id)
    donation = food_request.donation

    if donation.donor != request.user and not request.user.is_superuser:
        messages.error(request, "Unauthorized action.")
        return redirect('donor_dashboard')

    if request.method == 'POST':
        reason = request.POST.get('reject_reason', '').strip()
        food_request.status = 'REJECTED'
        food_request.donor_response_message = reason or "Request declined by donor."
        food_request.save()

        Notification.objects.create(
            recipient=food_request.ngo,
            title="Food Request Declined",
            message=f"Your request for '{donation.food_name}' was declined: {food_request.donor_response_message}",
            notification_type='REJECT',
            link="/dashboard/ngo/"
        )

        messages.info(request, "The food request has been declined.")
        return redirect('donation_detail', donation_id=donation.id)

    return render(request, 'requests/reject_confirm.html', {'food_request': food_request})


@login_required
def complete_request_view(request, request_id):
    """
    Marks the donation and pickup as fully completed.
    Creates a record in DonationHistory.
    """
    food_request = get_object_or_404(FoodRequest, id=request_id)
    donation = food_request.donation

    # Either donor or the assigned NGO or admin can confirm completion
    if request.user != donation.donor and request.user != food_request.ngo and not request.user.is_superuser:
        messages.error(request, "You are not authorized to mark this donation completed.")
        return redirect('dashboard_redirect')

    with transaction.atomic():
        food_request.status = 'COMPLETED'
        food_request.save()

        donation.status = 'COMPLETED'
        donation.save()

        # Create history record
        notes = request.POST.get('completion_notes', '').strip() or f"Successfully rescued and distributed by {food_request.ngo.profile.organization_name or food_request.ngo.username}"
        DonationHistory.objects.create(
            donation=donation,
            donor=donation.donor,
            receiver=food_request.ngo,
            quantity=donation.quantity,
            unit=donation.unit,
            notes=notes
        )

        # Notify donor and NGO
        Notification.objects.create(
            recipient=donation.donor,
            title="Food Rescue Completed!",
            message=f"The donation of '{donation.food_name}' ({donation.quantity} {donation.unit}) has been successfully completed. Thank you for saving food!",
            notification_type='COMPLETE',
            link="/donations/history/"
        )

        Notification.objects.create(
            recipient=food_request.ngo,
            title="Food Rescue Completed!",
            message=f"The pickup for '{donation.food_name}' has been marked completed. Thank you for your community service!",
            notification_type='COMPLETE',
            link="/donations/history/"
        )

    messages.success(request, f"Donation '{donation.food_name}' has been marked as COMPLETED! Food successfully rescued!")
    return redirect('donation_history')
