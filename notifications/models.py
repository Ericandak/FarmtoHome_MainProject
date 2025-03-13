from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('order', 'New Order'),
        ('product', 'Product Update'),
        ('user', 'User Activity'),
        ('system', 'System Notification'),
        ('milestone', 'Milestone Achievement'),  # Add this
        ('coupon', 'Coupon Reward'),  # Add this
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()} - {self.message[:50]}"

    class Meta:
        ordering = ['-created_at']