from django.db import models
from django.contrib.auth import get_user_model
from Products.models import Product
from Users.models import ShippingAddress

User = get_user_model()
# Create your models here.

class Order(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    consumer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.PROTECT, null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    delivery_status = models.CharField(max_length=10, choices=DELIVERY_STATUS_CHOICES, default='pending')

    def can_be_cancelled(self):
        return self.payment_status == 'pending' and self.delivery_status == 'pending'
    
    def __str__(self):
        return f"Order {self.id} by {self.consumer.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in Order {self.order.id}"
    
# Add these imports at the top
from django.db import models
from django.conf import settings
import uuid

class Milestone(models.Model):
    level = models.IntegerField()  # Number of orders needed
    discount_percentage = models.IntegerField()
    description = models.CharField(max_length=200)
    icon = models.CharField(max_length=50, default='fa-trophy')  # FontAwesome icon class

    class Meta:
        ordering = ['level']

    def __str__(self):
        return f"Level {self.level} - {self.discount_percentage}% discount"

class UserMilestone(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achieved_milestones')
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE)
    achieved_date = models.DateTimeField(auto_now_add=True)
    coupon_code = models.CharField(max_length=20, unique=True)
    is_used = models.BooleanField(default=False)
    expiry_date = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} - Level {self.milestone.level}"

    def save(self, *args, **kwargs):
        if not self.coupon_code:
            self.coupon_code = f"MILE{self.milestone.level}_{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)