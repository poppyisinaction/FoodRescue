from django.urls import path
from . import views

urlpatterns = [
    path('available/', views.available_donations_view, name='available_donations'),
    path('add/', views.add_donation_view, name='add_donation'),
    path('history/', views.donation_history_view, name='donation_history'),
    path('<int:donation_id>/', views.donation_detail_view, name='donation_detail'),
    path('<int:donation_id>/edit/', views.edit_donation_view, name='edit_donation'),
    path('<int:donation_id>/cancel/', views.cancel_donation_view, name='cancel_donation'),
]
