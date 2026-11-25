from django.urls import path
from . import views

urlpatterns = [
    path('create/<int:donation_id>/', views.create_request_view, name='create_request'),
    path('accept/<int:request_id>/', views.accept_request_view, name='accept_request'),
    path('reject/<int:request_id>/', views.reject_request_view, name='reject_request'),
    path('complete/<int:request_id>/', views.complete_request_view, name='complete_request'),
]
