from django.contrib import admin
from .models import Offer, OfferDetails, Order, Review

admin.site.register(Offer)
admin.site.register(OfferDetails)
admin.site.register(Order)
admin.site.register(Review)