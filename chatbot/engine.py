import json
import re
import urllib.request
import urllib.error
from django.conf import settings
from .models import ChatMessage

SYSTEM_INSTRUCTION = """
You are FoodRescue AI, a helpful, polite, and knowledgeable assistant for the FoodRescue platform.
Your objective is to help donors, NGOs, and volunteers reduce food waste and safely donate surplus food.
Follow these guidelines strictly:
1. Always prioritize food safety: cooked food must be kept either hot (>60°C) or chilled (<4°C), never donate spoiled or foul-smelling food.
2. Clearly explain how donors list food and how NGOs request food on the FoodRescue platform.
3. Be encouraging, concise, and structured with bullet points.
4. If asked about dangerous or contaminated food, strictly advise safe disposal, never consumption.
"""

# Rich rule-based knowledge base
KNOWLEDGE_RULES = [
    {
        'keywords': [r'how (to|do I) donate', r'donate food', r'post food', r'add donation', r'give food'],
        'response': """To donate food on FoodRescue, follow these easy steps:
1. **Sign Up / Log In**: Register an account with the role **Food Donor** (restaurants, caterers, hotels, or individuals).
2. **Click 'Donate Food'**: Go to your Donor Dashboard and tap **Add Donation**.
3. **Fill Food Details**: Provide the food name, category, quantity, preparation time, and strict **expiry time**.
4. **Specify Storage**: Select storage requirement (Room Temperature, Refrigerated, Frozen, or Insulated).
5. **Publish**: Once posted, local certified NGOs are notified and can request the food for immediate rescue!"""
    },
    {
        'keywords': [r'safety', r'safe', r'handling', r'temperature', r'spoil', r'hygiene', r'storage'],
        'response': """**Food Safety & Handling Guidelines:**
• **The 2-Hour Rule**: Cooked food should be chilled or consumed within 2 hours of preparation if kept at ambient room temperature.
• **Temperature Danger Zone**: Bacteria multiply rapidly between 5°C and 60°C (41°F - 140°F).
  - Cold items must stay below **4°C**.
  - Hot items must remain above **60°C**.
• **Packaging**: Use clean, airtight, food-grade containers or food-safe foil.
• **Visual & Odor Check**: Never donate food with off-odors, mold, unusual discoloration, or compromised packaging.
*Safety First*: When in doubt, throw it out – never distribute questionable food."""
    },
    {
        'keywords': [r'ngo', r'claim', r'request', r'receive', r'shelter', r'charity'],
        'response': """**How NGOs & Charitable Receivers Claim Food:**
1. **Register as NGO**: Create an account with the **NGO / Receiver** role and complete your profile.
2. **Browse Available Food**: Visit the **Available Food** catalog to see real-time surplus donations near your area.
3. **Submit Request**: Click **Request Food** on any listing, specifying your expected beneficiaries and estimated pickup time.
4. **Donor Review**: The donor reviews and accepts your request.
5. **Pickup & Confirmation**: Once collected, the pickup is marked as completed in the platform."""
    },
    {
        'keywords': [r'waste', r'reduce', r'tips', r'prevent', r'awareness', r'environment'],
        'response': """**Practical Ways to Reduce Food Waste:**
• **Plan Ahead**: Formulate realistic portion sizes and weekly meal plans.
• **First-In, First-Out (FIFO)**: Store newer groceries behind older ones to ensure older items are consumed first.
• **Proper Storage**: Understand expiration vs 'best before' dates; store herbs, root vegetables, and bread properly to extend shelf life.
• **Repurpose Leftovers**: Transform vegetable scraps into stocks and surplus fruit into smoothies or preserves.
• **Donate Early**: List surplus meals on **FoodRescue** as soon as an event concludes rather than waiting."""
    },
    {
        'keywords': [r'cost', r'free', r'charge', r'fee', r'price', r'money'],
        'response': """FoodRescue is a **100% non-profit community platform**. 
All services – including listing surplus food, requesting donations, and platform analytics – are completely **free of cost** for both donors and non-profit organizations."""
    },
    {
        'keywords': [r'verification', r'verified', r'account status', r'approve'],
        'response': """**Account Verification Details:**
• Newly registered donors and NGOs begin in **Pending Verification** status.
• Our platform administrators verify organization registration documents, food safety pledges, and contact authenticity.
• Verified organizations receive a **Verified Badge** that builds community trust and speeds up request approvals."""
    },
    {
        'keywords': [r'hello', r'hi', r'hey', r'greetings', r'who are you'],
        'response': """Hello! I am **FoodRescue AI**, your intelligent assistant dedicated to eliminating food hunger and reducing waste. 
You can ask me about:
• How to donate surplus food
• Food safety and temperature standards
• How NGOs can claim available meals
• Tips to prevent household and commercial food waste!"""
    }
]


def query_external_llm(prompt_text):
    """
    Attempts to call Google Gemini API or compatible LLM if key is configured.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '') or getattr(settings, 'LLM_API_KEY', '')
    if not api_key:
        return None

    # Google Gemini REST API endpoint
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{SYSTEM_INSTRUCTION}\n\nUser Question: {prompt_text}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 450
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=7) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                candidates = result.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        return parts[0].get('text', '').strip()
    except Exception as e:
        # Graceful fallback to rule-based engine
        pass
        
    return None


def get_ai_response(user_message, user=None, session_id=''):
    """
    Main entry point for FoodRescue AI.
    1. Try external LLM API if key configured.
    2. Fall back to rule-based expert matching if key missing or call fails.
    3. Persist interaction in ChatMessage.
    """
    clean_message = user_message.strip()
    response_text = None
    used_llm = False

    # Try external LLM API first if configured
    llm_output = query_external_llm(clean_message)
    if llm_output:
        response_text = llm_output
        used_llm = True
    else:
        # Rule-based fallback
        for rule in KNOWLEDGE_RULES:
            matched = False
            for pattern in rule['keywords']:
                if re.search(pattern, clean_message, re.IGNORECASE):
                    matched = True
                    break
            if matched:
                response_text = rule['response']
                break

        if not response_text:
            response_text = (
                "Thank you for contacting **FoodRescue AI**!\n\n"
                "I can assist with:\n"
                "• **Donating Food**: Listing your surplus meals and specifying pickup times.\n"
                "• **Food Safety**: Essential food handling, hygiene, and safe storage requirements.\n"
                "• **NGO Distribution**: How shelters and food banks can connect with local donors.\n"
                "• **Waste Prevention**: Practical everyday tips to reduce food waste.\n\n"
                "Could you please specify your question, or choose from one of the quick buttons below?"
            )

    # Save to ChatMessage database model
    try:
        ChatMessage.objects.create(
            user=user if (user and user.is_authenticated) else None,
            session_id=session_id,
            message=clean_message,
            response=response_text,
            used_llm=used_llm
        )
    except Exception:
        pass

    return response_text, used_llm
