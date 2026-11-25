from django.urls import path
from . import views

urlpatterns = [
    path('donor/', views.donor_dashboard_view, name='donor_dashboard'),
    path('ngo/', views.ngo_dashboard_view, name='ngo_dashboard'),
    path('admin/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/toggle-verify/<int:user_id>/', views.admin_toggle_verification, name='admin_toggle_verify'),
    path('admin/toggle-active/<int:user_id>/', views.admin_toggle_active, name='admin_toggle_active'),
]
