from django.db import models
from django.contrib.auth.models import AbstractUser,Group,Permission
# Create your models here.
class Role(models.Model):
    name = models.CharField(max_length=20, unique=True)
    def __str__(self):
        return self.name
class User(AbstractUser):
    role = models.ManyToManyField(Role)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    groups = models.ManyToManyField(Group, related_name='custom_user_groups')
    user_permissions = models.ManyToManyField(Permission, related_name='custom_user_permissions')


    def __str__(self):
        return self.username

class State(models.Model):
    name = models.CharField(max_length=50)  # State name
    country = models.CharField(max_length=100)  # Country name

    def __str__(self):
        return f"{self.name}, {self.country}"
class Address_table(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.TextField(null=True,blank=True)
    city = models.CharField(max_length=100,null=True,blank=True)
    zip_code = models.CharField(max_length=10,null=True,blank=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"{self.address}, {self.city}, {self.state}"
class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_addresses')
    full_name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    zip_code = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name}: {self.address}, {self.city}, {self.state}"

    class Meta:
        verbose_name_plural = "Shipping Addresses"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set is_default=False for all other addresses of this user
            ShippingAddress.objects.filter(user=self.user).update(is_default=False)
        super().save(*args, **kwargs)
class SellerDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    FarmName=models.CharField(max_length=15, blank=True, null=True)
    FarmAddress=models.CharField(max_length=100, blank=True, null=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE) 
    Farmcity = models.CharField(max_length=50, null=True, blank=True)
    Farmzip_code = models.CharField(max_length=20, null=True, blank=True) 

   
class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # Add this line if it's missing

    class Meta:
        ordering = ['timestamp']


class LicenseAuthenticationRequest(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='license_requests')
    license_file = models.FileField(upload_to='license_files/')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"License request for {self.seller.username} - {self.status}"
    
class ChatBotMessage(models.Model):
    SENDER_CHOICES = (
        ('USER', 'User'),
        ('BOT', 'Bot'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bot_messages')
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    sender = models.CharField(max_length=5, choices=SENDER_CHOICES)
    
    class Meta:
        ordering = ['timestamp']