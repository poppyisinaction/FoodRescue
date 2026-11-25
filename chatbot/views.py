from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from .engine import get_ai_response
from .models import ChatMessage


@csrf_exempt
@require_POST
def chat_api_view(request):
    """
    POST API endpoint for FoodRescue AI chatbot interactions.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_message = data.get('message', '').strip()
    except (ValueError, KeyError):
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    if not user_message:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)

    # Maintain session key for guest visitors
    if not request.session.session_key:
        request.session.save()
    session_id = request.session.session_key or 'anonymous'

    user = request.user if request.user.is_authenticated else None
    response_text, used_llm = get_ai_response(user_message, user=user, session_id=session_id)

    return JsonResponse({
        'success': True,
        'response': response_text,
        'used_llm': used_llm,
    })


@login_required
def chat_history_view(request):
    """
    View user's past chat conversations with FoodRescue AI.
    """
    if request.user.is_superuser:
        messages_list = ChatMessage.objects.all().order_by('-created_at')[:50]
    else:
        messages_list = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:30]

    return render(request, 'chatbot/chat_history.html', {'chat_messages': messages_list})
