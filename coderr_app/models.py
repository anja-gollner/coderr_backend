from django.db import models
from django.contrib.auth.models import User




class Offer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="Untitled Offer")  
    image = models.FileField(upload_to='uploads/', null=True, blank=True)    
    description = models.TextField(max_length=255, default="No description provided")  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]


class OfferDetails(models.Model):
    offer = models.ForeignKey(Offer, related_name='offer_details', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="Untitled Detail")  
    revisions = models.IntegerField(default=0)
    delivery_time_in_days = models.IntegerField(null=True, blank=True, default=1)  
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=50, null=True, blank=True, default="basic")  


class Order(models.Model):
    customer_user = models.ForeignKey(User, related_name='orders_as_customer', on_delete=models.CASCADE)
    business_user = models.ForeignKey(User, related_name='orders_as_business', on_delete=models.CASCADE)
    offer_detail = models.ForeignKey('OfferDetails', on_delete=models.CASCADE)

    title = models.CharField(max_length=255)
    revisions = models.IntegerField()
    delivery_time_in_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default='in_progress')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Review(models.Model):
    business_user = models.ForeignKey(User, related_name='reviews_received', on_delete=models.CASCADE)
    reviewer = models.ForeignKey(User, related_name='reviews_given', on_delete=models.CASCADE)
    rating = models.FloatField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    
    