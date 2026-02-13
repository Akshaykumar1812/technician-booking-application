from .models import Notification

def notifications_processor(request):
    notifications = []
    if request.session.get('user_id'):
        notifications = Notification.objects.filter(
            recipient_type__in=["users", "both"]
        ).order_by('-created_on')
    return {'notifications': notifications}

def technician_notifications_processor(request):
    notifications = []
    if request.session.get('technician_id'):
        notifications = Notification.objects.filter(
            recipient_type__in=["technicians", "both"]
        ).order_by('-created_on')
    return {'tech_notifications': notifications}