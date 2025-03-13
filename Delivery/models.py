from django.db import models
from Users.models import User
from django.utils import timezone
# Create your models here.
class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/')
    email = models.EmailField(max_length=254,null=True,blank=True)
    phone_number = models.CharField(max_length=15,null=True,blank=True)
    preferred_pincode = models.CharField(max_length=10)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} - {self.preferred_pincode}"
    
from django.db import models
from django.contrib.auth import get_user_model
from orders.models import Order

User = get_user_model()

class Delivery(models.Model):
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery')
    delivery_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='deliveries')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    assigned_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Delivery for Order {self.order.id} - {self.get_status_display()}"

    def start_delivery(self):
        self.status = 'in_transit'
        self.started_at = timezone.now()
        self.save()

    def complete_delivery(self):
        self.status = 'delivered'
        self.completed_at = timezone.now()
        self.order.delivery_status = 'delivered'
        self.order.save()
        self.save()

    def fail_delivery(self, reason):
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.notes = reason
        self.order.delivery_status = 'pending'
        self.order.save()
        self.save()
class DeliveryPerson(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_profile')
    primary_pincode = models.CharField(max_length=10)
    secondary_pincode = models.CharField(max_length=10, null=True, blank=True)
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_location_update = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.secondary_pincode:
            return f"{self.user.get_full_name()} - {self.primary_pincode}, {self.secondary_pincode}"
        return f"{self.user.get_full_name()} - {self.primary_pincode}"

    def get_active_pincodes(self):
        pincodes = [self.primary_pincode]
        if self.secondary_pincode:
            pincodes.append(self.secondary_pincode)
        return pincodes

    def update_location(self, latitude, longitude):
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.save()