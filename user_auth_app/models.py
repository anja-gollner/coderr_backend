from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    USER_TYPES = [
        ('business', 'Business'),
        ('customer', 'Customer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=255, default="default")
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True, default='')
    tel = models.CharField(max_length=20, null=True, blank=True, default='')
    description = models.TextField(null=True, blank=True, default='')
    working_hours = models.CharField(max_length=50, null=True, blank=True, default='8 - 16')
    type = models.CharField(max_length=10, choices=USER_TYPES, default='customer')  

    email = models.EmailField(unique=True, null=True, blank=True)  
    created_at = models.DateTimeField( default=timezone.now)  

    def __str__(self):
        return self.user.username