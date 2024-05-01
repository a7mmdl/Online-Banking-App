
from .models import Notification


def notifications(request):
    notifications = []
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user)
    return {'notifications': notifications}