from .models import Notification
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

import json

def notify_admin(notification_type, message):
    User = get_user_model()
    admin_users = User.objects.filter(is_staff=True)
    notifications = []
    for admin in admin_users:
        notification = Notification.objects.create(
            user=admin,
            notification_type=notification_type,
            message=message
        )
        notifications.append(notification)

    channel_layer = get_channel_layer()
    for notification in notifications:
        async_to_sync(channel_layer.group_send)(
            f"user_{notification.user.id}",
            {
                "type": "send_notification",
                "message": json.dumps({
                    "id": notification.id,
                    "type": notification.notification_type,
                    "message": notification.message,
                }),
            },
        )
def notify_milestone_achievement(user, milestone_level, coupon_code):
    """Send notification for milestone achievement"""
    message = f"Congratulations! You've reached {milestone_level} orders milestone! 🎉 Use coupon code: {coupon_code}"
    
    notification = Notification.objects.create(
        user=user,
        notification_type='milestone',
        message=message
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "send_notification",
            "message": json.dumps({
                "id": notification.id,
                "type": "milestone",
                "message": message,
                "milestone_level": milestone_level,
                "coupon_code": coupon_code
            }),
        },
    )