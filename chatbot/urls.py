from django.urls import path
from . import views

urlpatterns = [
    path('api/message/', views.chat_api_view, name='chatbot_api_message'),
    path('history/', views.chat_history_view, name='chat_history'),
]
