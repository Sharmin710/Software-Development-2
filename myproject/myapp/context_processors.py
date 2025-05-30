from .models import Notification

def notifications_processor(request):
    if request.user.is_authenticated:
        unread_notifications = request.user.recipient_notifications.filter(is_read=False)
        return {
            'notifications': request.user.recipient_notifications.order_by('-created_at')[:5],
            'unread_count': unread_notifications.count(),
        }
    return {}

