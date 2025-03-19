from rest_framework import serializers
from coderr_app.models import Offer, OfferDetails, Order, Review
from django.contrib.auth.models import User
from django.db.models import Min
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError


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
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    image = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Offer
        fields = ['id', 'user', 'title', 'image', 'description', 'created_at', 'updated_at', 'details', 'min_price', 'min_delivery_time', 'user_details']
        extra_kwargs = {"user": {"read_only": True}}

    def to_representation(self, instance):
        """Dynamisch anpassen, ob user_details oder nur user-ID angezeigt wird."""
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request and request.parser_context["view"].action == "list":
            data["user_details"] = {
                "first_name": instance.user.first_name,
                "last_name": instance.user.last_name,
                "username": instance.user.username
            }
        else:
            data.pop("user_details", None)
        return data


    def create(self, validated_data):
        """Custom create method to ensure basic, standard, and premium details exist."""
        details_data = self.initial_data.get('details', [])  
        user = self.context["request"].user  
        validated_data["user"] = user  

        required_types = {"basic", "standard", "premium"}
        existing_types = {detail.get("offer_type") for detail in details_data}

        for detail in details_data:
            if "offer_type" not in detail:
                raise ValidationError({"details": "Each offer detail must include an 'offer_type' field."})

        if not required_types.issubset(existing_types):
            raise ValidationError(
                {"details": "Offers must include 'basic', 'standard', and 'premium' offer types."}
            )

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

        if request and request.method in ["POST", "PUT"]:
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

        order = Order(
            id=offer_detail.id,
            customer_user=customer_user,
            business_user=business_user,
            offer_detail=offer_detail,
            title=offer.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,
            status='in_progress'
        )
        order.save(force_insert=True)

        return order

    def to_representation(self, instance):
        """ Ensure the full order details are returned in the response without offer_detail """
        data = {
            "id": instance.id,
            "customer_user": instance.customer_user.id,
            "business_user": instance.business_user.id,
            "title": instance.title,
            "revisions": instance.revisions,
            "delivery_time_in_days": instance.delivery_time_in_days,
            "price": instance.price,
            "features": instance.features,
            "offer_type": instance.offer_type,
            "status": instance.status,
            "created_at": instance.created_at,
            "updated_at": instance.updated_at,
        }
        return data

    
    
class UpdateOrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']

    def validate_status(self, value):
        valid_statuses = ['in_progress', 'completed', 'cancelled']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Ungültiger Status. Erlaubte Werte: {', '.join(valid_statuses)}")
        return value

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance  

    def to_representation(self, instance):
        return OrderSerializer(instance).data


class ReviewSerializer(serializers.ModelSerializer):
    reviewer = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'