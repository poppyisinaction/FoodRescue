# FoodRescue – AI-Powered Food Waste Management & Donation Platform

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.1%2B-green.svg)](https://djangoproject.com)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com)
[![License](https://img.shields.io/badge/License-MIT-orange.svg)](#)

> **BSc IT Third Year Research Project**  
> An intelligent full-stack web application connecting food donors (restaurants, hotels, supermarkets, caterers) with certified charitable receivers (NGOs, shelters, food banks) to eliminate food waste and fight hunger.

---

## 🌟 Key Highlights & Platform Features

### 1. Modern Commercial-Grade UI/UX
- **Design Theme**: Forest Green (`#176B45`), Light Green (`#E8F5E9`), Warm Orange Accent (`#F4A340`), and Dark Slate (`#263238`).
- **Responsive Layout**: Designed mobile-first using Bootstrap 5.3, Font Awesome 6.5, and Google Fonts (Poppins & Inter).
- **Interactive Dashboards**: Dynamic status and category analytics rendered using Chart.js.

### 2. Multi-Role Authentication & Access Control
- **Food Donors**: Restaurants, banquet halls, supermarkets, caterers, and individuals.
- **NGOs / Charitable Receivers**: Food banks, orphanages, and community shelters.
- **Platform Administrators**: Full platform management, verification toggles, and user activation controls.
- **Verification System**: Prevents unvetted entities from operating without administrative review.

### 3. Food Donation Lifecycle & Race-Condition Protection
- **Add Donation**: Captures food name, category, quantity, unit, food type (Veg, Non-Veg, Vegan), storage requirements, preparation datetime, strict expiry datetime, and pickup logistics.
- **Search & Filter**: Search by name/keywords, filter by category, dietary type, city, and sort by earliest expiry.
- **Concurrency & Race Condition Prevention**: When a donor accepts an NGO's request, the donation status atomically switches from `AVAILABLE` to `ACCEPTED`, and all competing pending claims are automatically resolved with notifications.
- **Pickup Confirmation**: Either party can mark collection completed, creating an immutable audit entry in `DonationHistory`.

### 4. FoodRescue AI – Intelligent Chatbot Assistant
- **Floating AI Assistant**: Available 24/7 across every page of the website with animated toggle and suggested prompt chips.
- **Dual-Engine Architecture**:
  1. **External LLM Integration**: Secure backend proxy to Google Gemini API or OpenAI-compatible LLM via `GEMINI_API_KEY` / `LLM_API_KEY`. API keys are strictly kept server-side and never exposed to the frontend.
  2. **Intelligent Rule-Based Fallback**: Built-in expert knowledge base providing verified guidelines on food safety, temperature thresholds (hot food >60°C, cold food <4°C), shelf life advice, and NGO claim instructions.
- **Chat Persistence**: Stores conversations in the `ChatMessage` model for accountability.

### 5. Custom Administrative Management Portal
- Real-time KPI counters: total users, donors, NGOs, donations by lifecycle state, and open support tickets.
- 1-click NGO verification and account suspension/activation.
- Contact message resolution.

---

## 📁 Project Architecture

```
FoodDonation2.0/
├── manage.py
├── requirements.txt
├── README.md
├── .env
├── db.sqlite3
│
├── foodrescue/                 # Project Settings & Route Configuration
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── accounts/                   # Authentication, UserProfile, Roles
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   └── urls.py
│
├── donations/                  # FoodDonation, DonationHistory, Listings
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   └── urls.py
│
├── food_requests/              # NGO Claims, Atomic State Locking
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── dashboard/                  # Donor, NGO, and Admin Dashboards
│   ├── views.py
│   └── urls.py
│
├── chatbot/                    # FoodRescue AI Engine & API Endpoint
│   ├── engine.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── notifications/              # Real-Time Event Alerts & Context Processor
│   ├── models.py
│   ├── context_processors.py
│   ├── views.py
│   └── urls.py
│
├── core/                       # Home, About, Contact & Demo Seeder
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── tests.py
│   └── management/commands/seed_data.py
│
├── templates/                  # Modular Bootstrap 5 Django Templates
│   ├── base.html
│   ├── home.html
│   ├── about.html
│   ├── contact.html
│   ├── accounts/
│   ├── donations/
│   ├── requests/
│   ├── dashboard/
│   ├── chatbot/
│   └── notifications/
│
├── static/                     # CSS, JS, Branding Assets
│   ├── css/style.css
│   ├── js/main.js
│   └── js/chatbot.js
│
└── media/                      # Uploaded Food & Profile Images
    ├── donations/
    └── profiles/
```

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| **Backend** | Python 3.12, Django 5.1+ |
| **Database** | SQLite (development) / PostgreSQL ready |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5.3, Font Awesome 6.5 |
| **Charts** | Chart.js 4.4 |
| **AI Engine** | Google Gemini API / Rule-Based NLP Expert Engine |
| **Security** | Django CSRF, password hashing (PBKDF2), atomic DB transactions |

---

## 🚀 Installation & Local Setup

### 1. Clone the Repository
```bash
git clone <repository_url>
cd FoodDonation2.0
```

### 2. Activate Virtual Environment
On Windows:
```powershell
.\venv\Scripts\activate
```
On Linux / macOS:
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` or edit the included `.env`:
```ini
DJANGO_SECRET_KEY=foodrescue-super-secure-production-secret-key-2026-xyz
DJANGO_DEBUG=True
DB_ENGINE=sqlite

# Optional: Add external Gemini / LLM key to enable cloud AI
GEMINI_API_KEY=
LLM_API_KEY=
```
*(Note: If no API key is specified, FoodRescue AI automatically uses its built-in rule-based expert engine seamlessly!)*

### 5. Apply Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Seed Demo Data (Users, Donations, Requests, History)
Run the automated database seeder:
```bash
python manage.py seed_data
```

### 7. Run the Development Server
```bash
python manage.py runserver
```
Visit **http://127.0.0.1:8000** in your browser!

---

## 🔑 Pre-Configured Demo Accounts

The database comes pre-seeded with realistic accounts for each user role:

| Role | Username | Password | Organization | Status |
|---|---|---|---|---|
| **Administrator** | `admin` | `admin123` | FoodRescue Global Operations | Verified |
| **Food Donor** | `taj_banquets` | `donorpassword123` | The Taj Palace Banquets | Verified |
| **Food Donor** | `greenleaf_bistro` | `donorpassword123` | GreenLeaf Organic Bistro | Verified |
| **Food Donor** | `freshbazaar_super` | `donorpassword123` | FreshBazaar Supermarket | Verified |
| **NGO / Receiver**| `aashray_ngo` | `ngopassword123` | Aashray Child Welfare | Verified |
| **NGO / Receiver**| `seva_foodbank` | `ngopassword123` | Seva Community Food Kitchen | Verified |

---

## 🧪 Automated Testing

Execute the test suite verifying all 10 core workflows:
```bash
python manage.py test core
```

Output:
```text
Ran 10 tests in 23.655s
OK
```

Tested capabilities include:
1. `test_homepage_loads`: Verifies home landing page, statistics, and food cards.
2. `test_about_page_loads`: Verifies About Us mission and impact statements.
3. `test_available_donations_filters`: Verifies multi-parameter catalog search and category filtering.
4. `test_user_registration`: Tests user sign up with profile creation and verification state.
5. `test_donor_add_food_donation`: Tests donor listing surplus food with expiry validations.
6. `test_ngo_claim_request_lifecycle`: Verifies end-to-end NGO claim, donor acceptance, and completion.
7. `test_chatbot_rule_based_fallback`: Verifies FoodRescue AI safe temperatures and donation advice.
8. `test_chatbot_api_endpoint`: Tests `/chatbot/api/message/` JSON API responses.
9. `test_contact_form_submission`: Verifies inquiries persist to database.
10. `test_admin_dashboard_access_control`: Verifies role-based access restrictions.

---

## 🎓 Academic Relevance (BSc IT Research Project)

This project exemplifies:
- **Full-Stack Software Architecture**: Separation of concerns across modular Django apps (`accounts`, `donations`, `food_requests`, `dashboard`, `chatbot`, `notifications`, `core`).
- **Database Engineering**: Normalized relational schema, foreign key cascades, unique constraints, and composite database indexes.
- **Concurrency & Concurrency Control**: Atomic database transactions preventing double-allocation race conditions during high-volume surplus events.
- **AI Integration**: Hybrid LLM proxy and rule-based fallback expert system preventing hallucination of hazardous food safety guidelines.
- **Social Impact**: Alignment with United Nations Sustainable Development Goals (SDG 2: Zero Hunger & SDG 12.3: Halving Global Food Waste).

---

## 📄 License
This project is licensed under the MIT License. Developed for research and educational purposes.
