def notifications_processor(request):
    """
    Context processor to make recent notifications and unread counts
    available on every template for authenticated users.
    """
    if request.user.is_authenticated:
        unread_notifications = request.user.notifications.filter(is_read=False)[:5]
        unread_count = request.user.notifications.filter(is_read=False).count()
        recent_notifications = request.user.notifications.all()[:10]
        return {
            'user_unread_notifications': unread_notifications,
            'user_unread_notification_count': unread_count,
            'user_recent_notifications': recent_notifications,
        }
    return {
        'user_unread_notifications': [],
        'user_unread_notification_count': 0,
        'user_recent_notifications': [],
    }
