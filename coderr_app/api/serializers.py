from rest_framework import serializers
from coderr_app.models import Offer, OfferDetails, Order, Review
from django.contrib.auth.models import User
from django.db.models import Min
from django.conf import settings
from django.urls import reverse





class OfferDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferDetails
        fields = ['id', 'title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type']


class OfferDetailsGETSerializer(serializers.ModelSerializer):
    """Serializer for GET requests: returns only ID and URL."""
    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetails
        fields = ['id', 'url']

    def get_url(self, obj):
        url = reverse('offerdetails-detail', args=[obj.id])
        return url.replace('/api', '')  
    

class OfferSerializer(serializers.ModelSerializer):
    details = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()
    min_price = serializers.FloatField(read_only=True)
    min_delivery_time = serializers.IntegerField(read_only=True)
    image = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Offer
        fields = '__all__'
        extra_kwargs = {"user": {"read_only": True}}


    def create(self, validated_data):
        """Custom create method to handle nested offer details."""
        details_data = self.initial_data.get('details', [])
        user = self.context["request"].user  
        validated_data["user"] = user 
        offer = Offer.objects.create(**validated_data)

        for detail_data in details_data:
            OfferDetails.objects.create(offer=offer, **detail_data)
        return offer  
    
    def update(self, instance, validated_data):
        """Custom update method to allow partial updates and handle nested OfferDetails."""

        details_data = validated_data.pop('offer_details', None)  
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if details_data is not None:
            existing_details = {detail.offer_type: detail for detail in instance.offer_details.all()}  

            for detail_data in details_data:
                offer_type = detail_data.get("offer_type")
                if offer_type in existing_details:
                    detail_instance = existing_details[offer_type]
                    for attr, value in detail_data.items():
                        setattr(detail_instance, attr, value)
                    detail_instance.save()
                else:
                    OfferDetails.objects.create(offer=instance, **detail_data)  

        return instance
    
    def get_details(self, obj):
        """Return different detail structures for list vs single offer requests."""
        request = self.context.get("request")
        
        # Handle single offer GET /offers/{id}/ or POST /offers/
        if request and (request.parser_context.get("kwargs", {}).get("pk") or request.method == "POST"):  
            return OfferDetailsSerializer(obj.offer_details.all(), many=True).data  

        return OfferDetailsGETSerializer(obj.offer_details.all(), many=True).data

    def get_user_details(self, obj):
        return {
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "username": obj.user.username
        }

    def get_min_price(self, obj):
        min_price = obj.offer_details.aggregate(min_price=Min('price'))['min_price']
        return float(min_price) if min_price is not None else 0.00

    def get_min_delivery_time(self, obj):
        min_time = obj.offer_details.aggregate(min_time=Min('delivery_time_in_days'))['min_time']
        return min_time if min_time is not None else 0
    
    def get_image(self, obj):
        """Ensure image URL includes MEDIA_URL"""
        if obj.image:
             request = self.context.get('request')  
             return request.build_absolute_uri(obj.image.url)  
        return None
    

class OrderSerializer(serializers.ModelSerializer):
    customer_user = serializers.PrimaryKeyRelatedField(read_only=True)
    business_user = serializers.PrimaryKeyRelatedField(read_only=True)
    title = serializers.CharField(read_only=True)
    revisions = serializers.IntegerField(read_only=True)
    delivery_time_in_days = serializers.IntegerField(read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    features = serializers.JSONField(read_only=True)
    offer_type = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = '__all__'


class CreateOrderSerializer(serializers.Serializer):
    offer_detail_id = serializers.IntegerField()

    def create(self, validated_data):
        offer_detail = OfferDetails.objects.get(id=validated_data['offer_detail_id'])
        offer = offer_detail.offer

        customer_user = self.context['request'].user
        business_user = offer.user  

        order = Order.objects.create(
            customer_user=customer_user,
            business_user=business_user,
            offer_detail=offer_detail,
            title=offer_detail.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,
            status='in_progress'
        )
        return order
    
    def to_representation(self, instance):
        """Ensure the full order details are returned in the response."""
        return OrderSerializer(instance).data 
    
    
class UpdateOrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']


class ReviewSerializer(serializers.ModelSerializer):
    reviewer = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'