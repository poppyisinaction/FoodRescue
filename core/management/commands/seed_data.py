from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserProfile
from donations.models import FoodDonation, DonationHistory
from food_requests.models import FoodRequest
from notifications.models import Notification
from core.models import ContactMessage
from chatbot.models import ChatMessage


class Command(BaseCommand):
    help = "Seeds database with demo users, roles, surplus food donations, claims, and history."

    def handle(self, *args, **options):
        self.stdout.write("Seeding FoodRescue platform database...")

        # 1. Superuser / Admin
        admin_user, created = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@foodrescue.org',
            'first_name': 'Platform',
            'last_name': 'Administrator',
            'is_staff': True,
            'is_superuser': True
        })
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            admin_profile = admin_user.profile
            admin_profile.role = 'ADMIN'
            admin_profile.verification_status = 'VERIFIED'
            admin_profile.organization_name = 'FoodRescue Global Operations'
            admin_profile.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin / admin123"))

        # 2. Donors
        donors_data = [
            {
                'username': 'taj_banquets',
                'email': 'banquets@tajpalace.com',
                'password': 'donorpassword123',
                'name': 'The Taj Palace Banquets',
                'type': 'Luxury Hotel & Caterer',
                'city': 'Mumbai',
                'address': 'Apollo Bunder, Colaba, Mumbai 400001',
                'phone': '+91 22 6665 3366',
                'status': 'VERIFIED'
            },
            {
                'username': 'greenleaf_bistro',
                'email': 'hello@greenleafbistro.in',
                'password': 'donorpassword123',
                'name': 'GreenLeaf Organic Bistro',
                'type': 'Restaurant & Bakery',
                'city': 'Mumbai',
                'address': 'Pali Hill, Bandra West, Mumbai 400050',
                'phone': '+91 98200 45678',
                'status': 'VERIFIED'
            },
            {
                'username': 'freshbazaar_super',
                'email': 'ops@freshbazaar.com',
                'password': 'donorpassword123',
                'name': 'FreshBazaar Supermarket',
                'type': 'Supermarket & Grocery Chain',
                'city': 'Mumbai',
                'address': 'Link Road, Andheri West, Mumbai 400053',
                'phone': '+91 99300 11223',
                'status': 'VERIFIED'
            },
            {
                'username': 'royal_caterers',
                'email': 'info@royalcaterers.org',
                'password': 'donorpassword123',
                'name': 'Royal Feast Catering',
                'type': 'Event Organizer',
                'city': 'Mumbai',
                'address': 'Dadar TT Circle, Dadar East, Mumbai 400014',
                'phone': '+91 98199 87654',
                'status': 'PENDING'
            }
        ]

        created_donors = {}
        for d in donors_data:
            user, u_created = User.objects.get_or_create(username=d['username'], defaults={
                'email': d['email'],
                'first_name': d['name'].split()[0],
                'last_name': 'Donor'
            })
            if u_created:
                user.set_password(d['password'])
                user.save()
            profile = user.profile
            profile.role = 'DONOR'
            profile.organization_name = d['name']
            profile.organization_type = d['type']
            profile.city = d['city']
            profile.address = d['address']
            profile.phone = d['phone']
            profile.verification_status = d['status']
            profile.save()
            created_donors[d['username']] = user

        # 3. NGOs
        ngos_data = [
            {
                'username': 'aashray_ngo',
                'email': 'contact@aashrayfoundation.org',
                'password': 'ngopassword123',
                'name': 'Aashray Child Welfare & Shelter',
                'type': 'Orphanage & Children Shelter',
                'city': 'Mumbai',
                'address': 'Station Road, Kurla West, Mumbai 400070',
                'phone': '+91 98211 55443',
                'status': 'VERIFIED'
            },
            {
                'username': 'seva_foodbank',
                'email': 'meals@sevafoodbank.in',
                'password': 'ngopassword123',
                'name': 'Seva Community Food Kitchen',
                'type': 'Community Kitchen & Food Bank',
                'city': 'Mumbai',
                'address': '90 Feet Road, Dharavi, Mumbai 400017',
                'phone': '+91 98333 77889',
                'status': 'VERIFIED'
            },
            {
                'username': 'roti_bank_mumbai',
                'email': 'help@rotibankmumbai.org',
                'password': 'ngopassword123',
                'name': 'Roti Bank Charitable Trust',
                'type': 'Homeless Hunger Relief',
                'city': 'Mumbai',
                'address': 'Hindmata, Parel, Mumbai 400012',
                'phone': '+91 98222 99001',
                'status': 'VERIFIED'
            }
        ]

        created_ngos = {}
        for n in ngos_data:
            user, u_created = User.objects.get_or_create(username=n['username'], defaults={
                'email': n['email'],
                'first_name': n['name'].split()[0],
                'last_name': 'NGO'
            })
            if u_created:
                user.set_password(n['password'])
                user.save()
            profile = user.profile
            profile.role = 'NGO'
            profile.organization_name = n['name']
            profile.organization_type = n['type']
            profile.city = n['city']
            profile.address = n['address']
            profile.phone = n['phone']
            profile.verification_status = n['status']
            profile.save()
            created_ngos[n['username']] = user

        # 4. Food Donations
        now = timezone.now()
        donations_specs = [
            {
                'donor': created_donors['taj_banquets'],
                'name': '75 Portions Royal Vegetable Biryani with Mirchi Salan',
                'category': 'COOKED_MEALS',
                'food_type': 'VEG',
                'quantity': 75.0,
                'unit': 'meals',
                'desc': 'Prepared for an evening corporate seminar buffet. Stored in hot insulated stainless steel cambros at 65°C. Pure vegetarian, cooked with basmati rice, seasonal vegetables, and mild aromatic spices.',
                'prep_offset': -2,
                'exp_offset': 6,
                'location': 'Taj Palace Banquets, Apollo Bunder, Colaba',
                'pickup_time': 'Today, 8:30 PM - 10:30 PM',
                'storage': 'INSULATED',
                'status': 'AVAILABLE'
            },
            {
                'donor': created_donors['greenleaf_bistro'],
                'name': '45 Fresh Sourdough Loaves & Assorted Croissants',
                'category': 'BAKERY',
                'food_type': 'VEGAN',
                'quantity': 45.0,
                'unit': 'packets',
                'desc': 'Artisan whole wheat sourdough and fresh breakfast pastries baked early this morning. Packed in food-grade kraft paper bags. Best consumed within 24-48 hours.',
                'prep_offset': -6,
                'exp_offset': 36,
                'location': 'GreenLeaf Bistro, Pali Hill, Bandra West',
                'pickup_time': 'Today before 11:00 PM',
                'storage': 'ROOM_TEMP',
                'status': 'AVAILABLE'
            },
            {
                'donor': created_donors['freshbazaar_super'],
                'name': '120 kg Fresh Farm Produce (Apples, Bananas & Spinach)',
                'category': 'PRODUCE',
                'food_type': 'VEGAN',
                'quantity': 120.0,
                'unit': 'kg',
                'desc': 'Surplus ripe fruit crates and fresh leaf greens. Ideal for community shelters, smoothie prep, or community kitchens. Sorted and crate-packed.',
                'prep_offset': -12,
                'exp_offset': 48,
                'location': 'FreshBazaar Distribution Bay 3, Andheri West',
                'pickup_time': 'Tomorrow 9:00 AM - 1:00 PM',
                'storage': 'REFRIGERATED',
                'status': 'AVAILABLE'
            },
            {
                'donor': created_donors['royal_caterers'],
                'name': '50 Portions Paneer Makhani & Tandoori Roti Packs',
                'category': 'COOKED_MEALS',
                'food_type': 'VEG',
                'quantity': 50.0,
                'unit': 'meals',
                'desc': 'Wedding reception excess. Kept hot above 60°C. Individual meal meal-boxes with paneer curry, 3 rotis, and pickle.',
                'prep_offset': -3,
                'exp_offset': 5,
                'location': 'Dadar TT Circle banquet premises',
                'pickup_time': 'Urgent: Pickup by 9:30 PM',
                'storage': 'INSULATED',
                'status': 'ACCEPTED'
            },
            {
                'donor': created_donors['taj_banquets'],
                'name': '60 Portions Dal Tadka and Jeera Rice',
                'category': 'COOKED_MEALS',
                'food_type': 'VEG',
                'quantity': 60.0,
                'unit': 'meals',
                'desc': 'Homestyle yellow lentil tadka and aromatic cumin rice from afternoon banquet service.',
                'prep_offset': -24,
                'exp_offset': -12,
                'location': 'Taj Palace Back Gate, Colaba',
                'pickup_time': 'Yesterday afternoon',
                'storage': 'ROOM_TEMP',
                'status': 'COMPLETED'
            }
        ]

        created_donations = []
        for ds in donations_specs:
            donation, d_created = FoodDonation.objects.get_or_create(
                food_name=ds['name'],
                defaults={
                    'donor': ds['donor'],
                    'category': ds['category'],
                    'food_type': ds['food_type'],
                    'quantity': ds['quantity'],
                    'unit': ds['unit'],
                    'description': ds['desc'],
                    'preparation_datetime': now + timedelta(hours=ds['prep_offset']),
                    'expiry_datetime': now + timedelta(hours=ds['exp_offset']),
                    'pickup_location': ds['location'],
                    'pickup_time': ds['pickup_time'],
                    'storage_requirements': ds['storage'],
                    'status': ds['status'],
                    'contact_person': ds['donor'].first_name,
                    'contact_phone': ds['donor'].profile.phone
                }
            )
            created_donations.append(donation)

        # 5. Food Requests
        # Request on Accepted donation (Paneer Makhani)
        accepted_donation = created_donations[3]
        req1, _ = FoodRequest.objects.get_or_create(
            donation=accepted_donation,
            ngo=created_ngos['aashray_ngo'],
            defaults={
                'request_message': 'We have 45 underprivileged children at our Kurla shelter waiting for evening dinner. Our transport van is 15 minutes away.',
                'estimated_pickup_time': 'Tonight at 8:45 PM',
                'status': 'ACCEPTED',
                'donor_response_message': 'Approved! Please contact Chef Arvind at the dispatch gate.'
            }
        )

        # Request on completed donation
        completed_donation = created_donations[4]
        req2, _ = FoodRequest.objects.get_or_create(
            donation=completed_donation,
            ngo=created_ngos['seva_foodbank'],
            defaults={
                'request_message': 'Distributed to senior citizens and night-shelter residents at Dharavi community center.',
                'estimated_pickup_time': 'Yesterday 4:00 PM',
                'status': 'COMPLETED',
                'donor_response_message': 'Collected on time. Thank you!'
            }
        )

        # Donation History entry
        DonationHistory.objects.get_or_create(
            donation=completed_donation,
            donor=completed_donation.donor,
            receiver=created_ngos['seva_foodbank'],
            defaults={
                'quantity': completed_donation.quantity,
                'unit': completed_donation.unit,
                'notes': 'Successfully distributed 60 fresh meals to Dharavi night shelter. Zero waste achieved.'
            }
        )

        # 6. Sample Notifications
        Notification.objects.get_or_create(
            recipient=created_donors['royal_caterers'],
            title='Request Accepted',
            defaults={
                'message': 'Aashray Child Welfare has been assigned to collect your 50 Paneer Makhani packs.',
                'notification_type': 'ACCEPT',
                'link': f'/donations/{accepted_donation.id}/'
            }
        )

        Notification.objects.get_or_create(
            recipient=created_ngos['aashray_ngo'],
            title='Claim Approved!',
            defaults={
                'message': 'Your claim for 50 Portions Paneer Makhani was ACCEPTED. Pickup window: by 9:30 PM.',
                'notification_type': 'ACCEPT',
                'link': f'/donations/{accepted_donation.id}/'
            }
        )

        # 7. Sample Contact Messages
        ContactMessage.objects.get_or_create(
            name='Rohit Sharma',
            email='rohit.caterers@gmail.com',
            subject='Bulk Wedding Donation Inquiry',
            defaults={
                'message': 'We organize large destination weddings with frequent 100+ meal surpluses. Can FoodRescue arrange refrigerated transport trucks?',
                'is_resolved': False
            }
        )

        # 8. Sample Chatbot Messages
        ChatMessage.objects.get_or_create(
            message='What are the temperature safety guidelines for donating cooked food?',
            defaults={
                'response': 'Food safety rules require cooked food to be maintained either hot (above 60°C) or rapidly chilled (below 4°C). The 2-hour window rule applies to room temperature exposure.',
                'used_llm': False
            }
        )

        self.stdout.write(self.style.SUCCESS("Database seeded successfully with realistic demo data!"))
