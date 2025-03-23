from django.utils import timezone
from datetime import timedelta
from .models import Milestone, UserMilestone
from notifications.utils import notify_admin
from django.db.models import Count

def check_order_milestone(user):
    """
    Check if user has reached a milestone and create rewards
    """
    # Get total completed orders for the user
    order_count = user.orders.filter(payment_status='completed').count()
    
    # Define milestone levels if not in database
    default_milestones = {
        5: 10,   # 5 orders = 10% discount
        10: 15,  # 10 orders = 15% discount
        20: 20,  # 20 orders = 20% discount
        30: 25   # 30 orders = 25% discount
    }

    # Ensure milestones exist in database
    for level, discount in default_milestones.items():
        Milestone.objects.get_or_create(
            level=level,
            defaults={
                'discount_percentage': discount,
                'description': f"Complete {level} orders to get {discount}% discount!",
            }
        )

    # Check each milestone
    for milestone in Milestone.objects.all():
        if order_count == milestone.level:
            # Check if user already has this milestone
            if not UserMilestone.objects.filter(user=user, milestone=milestone).exists():
                # Create new milestone achievement
                user_milestone = UserMilestone.objects.create(
                    user=user,
                    milestone=milestone,
                    expiry_date=timezone.now() + timedelta(days=30)
                )

                # Create notification
                notification_message = (
                    f"🎉 Congratulations! You've completed {milestone.level} orders! "
                    f"Use code {user_milestone.coupon_code} to get {milestone.discount_percentage}% off your next order. "
                    f"Valid for 30 days!"
                )
                
                from notifications.models import Notification
                Notification.objects.create(
                    user=user,
                    notification_type='milestone',
                    message=notification_message
                )

                return user_milestone
    
    return None