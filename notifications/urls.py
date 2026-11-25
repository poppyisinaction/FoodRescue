from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_list_view, name='notifications_list'),
    path('mark-read/<int:notification_id>/', views.mark_notification_read_api, name='mark_notification_read'),
    path('mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
]
