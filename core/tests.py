from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
import json
from accounts.models import UserProfile
from donations.models import FoodDonation, DonationHistory
from donations.forms import FoodDonationForm
from food_requests.models import FoodRequest
from notifications.models import Notification
from core.models import ContactMessage
from chatbot.engine import get_ai_response


class FoodRescuePlatformTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Donor
        self.donor_user = User.objects.create_user(
            username='test_donor',
            email='donor@test.com',
            password='testpassword123'
        )
        self.donor_profile = self.donor_user.profile
        self.donor_profile.role = 'DONOR'
        self.donor_profile.organization_name = 'Test Bistro'
        self.donor_profile.verification_status = 'VERIFIED'
        self.donor_profile.save()

        # Create NGO 1
        self.ngo_user = User.objects.create_user(
            username='test_ngo',
            email='ngo@test.com',
            password='testpassword123'
        )
        self.ngo_profile = self.ngo_user.profile
        self.ngo_profile.role = 'NGO'
        self.ngo_profile.organization_name = 'Test Hope Shelter'
        self.ngo_profile.verification_status = 'VERIFIED'
        self.ngo_profile.save()

        # Create NGO 2 (for race-condition testing)
        self.ngo_user_2 = User.objects.create_user(
            username='test_ngo_2',
            email='ngo2@test.com',
            password='testpassword123'
        )
        self.ngo_profile_2 = self.ngo_user_2.profile
        self.ngo_profile_2.role = 'NGO'
        self.ngo_profile_2.organization_name = 'Seva Roti Kitchen'
        self.ngo_profile_2.verification_status = 'VERIFIED'
        self.ngo_profile_2.save()

        # Create Admin
        self.admin_user = User.objects.create_superuser(
            username='test_admin',
            email='admin@test.com',
            password='adminpassword123'
        )
        self.admin_profile = self.admin_user.profile
        self.admin_profile.role = 'ADMIN'
        self.admin_profile.save()

        # Create an available Food Donation
        now = timezone.now()
        self.donation = FoodDonation.objects.create(
            donor=self.donor_user,
            food_name='30 Portions Veg Khichdi',
            category='COOKED_MEALS',
            food_type='VEG',
            quantity=30.0,
            unit='meals',
            description='Warm, nutritious freshly prepared dal khichdi',
            preparation_datetime=now,
            expiry_datetime=now + timedelta(hours=6),
            pickup_location='Bandra West, Mumbai',
            pickup_time='Today 5 PM - 8 PM',
            storage_requirements='INSULATED',
            status='AVAILABLE'
        )

    def test_homepage_loads(self):
        """Test landing page renders successfully with live statistics."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Save Food. Share Hope. Fight Hunger.")
        self.assertContains(response, "30 Portions Veg Khichdi")

    def test_about_page_loads(self):
        """Test About Us page renders properly."""
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ending Food Waste. Nourishing Communities.")

    def test_available_donations_filters(self):
        """Test available donations catalog with category and search filter."""
        response = self.client.get('/available-food/?category=COOKED_MEALS')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "30 Portions Veg Khichdi")

        # Non-matching search
        response_empty = self.client.get('/available-food/?q=NonExistentPizzaBatch')
        self.assertEqual(response_empty.status_code, 200)
        self.assertNotContains(response_empty, "30 Portions Veg Khichdi")

    def test_user_registration(self):
        """Test user registration flow for an NGO."""
        response = self.client.post('/register/', {
            'username': 'new_ngo_user',
            'first_name': 'New',
            'last_name': 'NGO',
            'email': 'newngo@test.com',
            'role': 'NGO',
            'organization_name': 'Sunrise Community Foundation',
            'organization_type': 'Shelter',
            'phone': '+91 9988776655',
            'city': 'Mumbai',
            'address': 'Dadar, Mumbai',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username='new_ngo_user')
        self.assertEqual(new_user.profile.role, 'NGO')
        self.assertEqual(new_user.profile.organization_name, 'Sunrise Community Foundation')

    def test_donor_add_food_donation(self):
        """Test authorized donor creating a new food donation."""
        self.client.login(username='test_donor', password='testpassword123')
        now = timezone.now()
        response = self.client.post('/donate-food/', {
            'food_name': '25 Vegetable Sandwiches',
            'category': 'BAKERY',
            'food_type': 'VEG',
            'quantity': 25.0,
            'unit': 'packets',
            'description': 'Freshly prepared cucumber and tomato sandwiches.',
            'preparation_datetime': now.strftime('%Y-%m-%dT%H:%M'),
            'expiry_datetime': (now + timedelta(hours=8)).strftime('%Y-%m-%dT%H:%M'),
            'pickup_location': 'Bandra West Bakery counter',
            'pickup_time': 'Today 6 PM - 9 PM',
            'storage_requirements': 'ROOM_TEMP',
            'contact_person': 'Chef Rahul',
            'contact_phone': '+91 98765 00000',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(FoodDonation.objects.filter(food_name='25 Vegetable Sandwiches').exists())

    def test_ngo_claim_request_lifecycle(self):
        """
        Test the end-to-end claim lifecycle:
        1. NGO requests available food.
        2. Donor accepts request -> donation status updates to ACCEPTED.
        3. Pickup completed -> creates DonationHistory.
        """
        # 1. NGO submits claim
        self.client.login(username='test_ngo', password='testpassword123')
        req_response = self.client.post(f'/requests/create/{self.donation.id}/', {
            'request_message': 'We will collect this for 30 children at our shelter.',
            'estimated_pickup_time': 'Today 6:30 PM'
        })
        self.assertEqual(req_response.status_code, 302)
        claim = FoodRequest.objects.get(donation=self.donation, ngo=self.ngo_user)
        self.assertEqual(claim.status, 'PENDING')

        # 2. Donor accepts claim
        self.client.login(username='test_donor', password='testpassword123')
        accept_response = self.client.post(f'/requests/accept/{claim.id}/', {
            'donor_response_message': 'Approved! Please collect from side gate.'
        })
        self.assertEqual(accept_response.status_code, 302)
        claim.refresh_from_db()
        self.donation.refresh_from_db()
        self.assertEqual(claim.status, 'ACCEPTED')
        self.assertEqual(self.donation.status, 'ACCEPTED')

        # 3. Complete pickup
        complete_response = self.client.post(f'/requests/complete/{claim.id}/', {
            'completion_notes': 'Verified pickup by NGO van.'
        })
        self.assertEqual(complete_response.status_code, 302)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'COMPLETED')
        self.assertTrue(DonationHistory.objects.filter(donation=self.donation).exists())

    def test_race_condition_competing_ngo_requests(self):
        """
        Test that when multiple NGOs request the same food donation,
        accepting one automatically marks competing requests as REJECTED
        and prevents any additional NGOs from requesting.
        """
        # NGO 1 requests
        self.client.login(username='test_ngo', password='testpassword123')
        self.client.post(f'/requests/create/{self.donation.id}/', {
            'request_message': 'NGO 1 request for shelter.',
            'estimated_pickup_time': '5:00 PM'
        })

        # NGO 2 requests the same donation
        self.client.login(username='test_ngo_2', password='testpassword123')
        self.client.post(f'/requests/create/{self.donation.id}/', {
            'request_message': 'NGO 2 request for community kitchen.',
            'estimated_pickup_time': '5:30 PM'
        })

        req1 = FoodRequest.objects.get(donation=self.donation, ngo=self.ngo_user)
        req2 = FoodRequest.objects.get(donation=self.donation, ngo=self.ngo_user_2)
        self.assertEqual(req1.status, 'PENDING')
        self.assertEqual(req2.status, 'PENDING')

        # Donor accepts NGO 1
        self.client.login(username='test_donor', password='testpassword123')
        self.client.post(f'/requests/accept/{req1.id}/')

        req1.refresh_from_db()
        req2.refresh_from_db()
        self.donation.refresh_from_db()

        self.assertEqual(req1.status, 'ACCEPTED')
        self.assertEqual(req2.status, 'REJECTED')
        self.assertEqual(self.donation.status, 'ACCEPTED')

        # NGO 3 tries to request already accepted donation
        ngo3 = User.objects.create_user(username='ngo3', email='ngo3@test.com', password='pw')
        ngo3.profile.role = 'NGO'
        ngo3.profile.save()
        self.client.login(username='ngo3', password='pw')
        res = self.client.post(f'/requests/create/{self.donation.id}/', {
            'request_message': 'Too late request'
        })
        # Should redirect with warning that it is no longer available
        self.assertEqual(res.status_code, 302)

    def test_donation_cancellation_workflow(self):
        """Test donor cancelling a donation listing."""
        # Create request first
        self.client.login(username='test_ngo', password='testpassword123')
        self.client.post(f'/requests/create/{self.donation.id}/', {
            'request_message': 'Pending before cancel',
            'estimated_pickup_time': 'Soon'
        })

        # Donor cancels
        self.client.login(username='test_donor', password='testpassword123')
        cancel_res = self.client.get(f'/donations/{self.donation.id}/cancel/')
        self.assertEqual(cancel_res.status_code, 302)

        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'CANCELLED')

        req = FoodRequest.objects.get(donation=self.donation, ngo=self.ngo_user)
        self.assertEqual(req.status, 'CANCELLED')

    def test_image_upload_validation(self):
        """Test form-level image format validation."""
        fake_executable = SimpleUploadedFile(
            "malicious.exe",
            b"fake binary content",
            content_type="application/octet-stream"
        )
        now = timezone.now()
        form_data = {
            'food_name': 'Test Dish',
            'category': 'COOKED_MEALS',
            'food_type': 'VEG',
            'quantity': 10,
            'unit': 'meals',
            'description': 'Test',
            'preparation_datetime': now.strftime('%Y-%m-%dT%H:%M'),
            'expiry_datetime': (now + timedelta(hours=4)).strftime('%Y-%m-%dT%H:%M'),
            'pickup_location': 'Mumbai',
            'pickup_time': 'Now',
            'storage_requirements': 'ROOM_TEMP'
        }
        form = FoodDonationForm(data=form_data, files={'image': fake_executable})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_notification_mark_read_api(self):
        """Test marking a notification as read via POST API."""
        notif = Notification.objects.create(
            recipient=self.donor_user,
            title='Test Alert',
            message='You have an alert.',
            notification_type='SYSTEM'
        )
        self.client.login(username='test_donor', password='testpassword123')
        res = self.client.post(f'/notifications/mark-read/{notif.id}/')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_admin_toggle_verify_and_active(self):
        """Test admin toggling organization verification and account active status."""
        self.client.login(username='test_admin', password='adminpassword123')

        # Toggle verify
        res_v = self.client.get(f'/dashboard/admin/toggle-verify/{self.donor_user.id}/')
        self.assertEqual(res_v.status_code, 302)
        self.donor_user.profile.refresh_from_db()
        self.assertEqual(self.donor_user.profile.verification_status, 'PENDING')

        # Toggle active
        res_a = self.client.get(f'/dashboard/admin/toggle-active/{self.donor_user.id}/')
        self.assertEqual(res_a.status_code, 302)
        self.donor_user.refresh_from_db()
        self.assertFalse(self.donor_user.is_active)

    def test_chatbot_rule_based_fallback(self):
        """Test that FoodRescue AI gives smart, accurate answers via rule-based fallback."""
        response_text, used_llm = get_ai_response("How do I donate food on FoodRescue?")
        self.assertIn("Food Donor", response_text)
        self.assertIn("Add Donation", response_text)

        # Safety question
        safety_text, _ = get_ai_response("What are the temperature safety rules?")
        self.assertIn("60°C", safety_text)
        self.assertIn("4°C", safety_text)

    def test_chatbot_api_endpoint(self):
        """Test POST /chatbot/api/message/ returns valid JSON."""
        response = self.client.post(
            '/chatbot/api/message/',
            data=json.dumps({'message': 'How can an NGO claim food?'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn("NGO", data['response'])

    def test_contact_form_submission(self):
        """Test inquiry submission on Contact Us page."""
        response = self.client.post('/contact/', {
            'name': 'Priya Patel',
            'email': 'priya@example.com',
            'subject': 'Volunteer Distribution Driver',
            'message': 'I have a cargo van and want to help transport food on weekends.'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ContactMessage.objects.filter(email='priya@example.com').exists())

    def test_admin_dashboard_access_control(self):
        """Non-admin users must not access custom admin dashboard."""
        self.client.login(username='test_donor', password='testpassword123')
        response = self.client.get('/dashboard/admin/')
        self.assertEqual(response.status_code, 302)

        # Superuser should access smoothly
        self.client.login(username='test_admin', password='adminpassword123')
        response_admin = self.client.get('/dashboard/admin/')
        self.assertEqual(response_admin.status_code, 200)
        self.assertContains(response_admin, "Executive Control Center")
