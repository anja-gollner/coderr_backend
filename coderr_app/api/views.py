from rest_framework import viewsets, filters, status, permissions
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from coderr_app.models import Offer, OfferDetails, Order, Review
from user_auth_app.models import UserProfile
from .serializers import OfferSerializer, OfferDetailsSerializer, OrderSerializer, CreateOrderSerializer, UpdateOrderStatusSerializer, ReviewSerializer
from rest_framework.permissions import IsAuthenticated
from .permissions import IsBusinessOwnerOrAdmin, IsCustomerOrAdmin, IsReviewerOrAdmin
from .pagination import CustomPageNumberPagination  
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Avg
from django.db.models import Min, Q
from rest_framework.exceptions import PermissionDenied




class OfferViewset(viewsets.ModelViewSet):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    permission_classes = [IsAuthenticated, IsBusinessOwnerOrAdmin]
    pagination_class = CustomPageNumberPagination

    filterset_fields = {
        'user': ['exact'], 
        'updated_at': ['gte'],
        'offer_details__price': ['gte'],  
        'offer_details__delivery_time_in_days': ['exact', 'lte', 'gte']
    }
    search_fields = ['title', 'description']
    ordering_fields = ['min_price', 'updated_at']

    def get_queryset(self):
        queryset = Offer.objects.annotate(
            min_price=Min('offer_details__price'), 
            min_delivery_time=Min('offer_details__delivery_time_in_days')
        )

        creator_id = self.request.query_params.get('creator_id')
        max_delivery_time = self.request.query_params.get('max_delivery_time')

        if creator_id:
            queryset = queryset.filter(user_id=creator_id)

        if max_delivery_time:
            queryset = queryset.filter(offer_details__delivery_time_in_days__lte=max_delivery_time)

        return queryset


    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        

class OfferDetailsViewSet(viewsets.ModelViewSet):
    queryset = OfferDetails.objects.all()
    serializer_class = OfferDetailsSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    def get_queryset(self):
        return Order.objects.filter(
            Q(customer_user=self.request.user) | Q(business_user=self.request.user)  
        )
    
    def get_permissions(self):
        if self.action in ['create']:
            return [IsCustomerOrAdmin()]
        return [permissions.IsAuthenticated()]  
    
    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == 'create':
            return CreateOrderSerializer
        if self.action == 'partial_update':  
            return UpdateOrderStatusSerializer
        return OrderSerializer
    
    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = self.get_serializer_context()
        return super().get_serializer(*args, **kwargs)


    def perform_create(self, serializer):
        """ Ensure only customers can create orders and assign the customer user """
        user_profile = getattr(self.request.user, 'profile', None)
        if not user_profile or user_profile.type != 'customer':
            raise PermissionDenied("Only customers can create orders.")
        
        serializer.save()



class OrderCountView(APIView):
    def get(self, request, business_user_id): 
        business_user = get_object_or_404(User, id=business_user_id)
        order_count = Order.objects.filter(business_user=business_user, status='in_progress').count()
        return Response({"order_count": order_count}, status=status.HTTP_200_OK)
    

class CompletedOrderCountView(APIView):
    def get(self, request, business_user_id):
        business_user = get_object_or_404(User, id=business_user_id)
        completed_order_count = Order.objects.filter(business_user=business_user, status='completed').count()
        return Response({"completed_order_count": completed_order_count}, status=status.HTTP_200_OK)
    

class BaseInfoViewset(APIView):
    def get(self, request):
        review_count = Review.objects.count()
        average_rating = Review.objects.aggregate(avg_rating=Avg('rating'))['avg_rating']
        average_rating = round(average_rating, 1) if average_rating is not None else 0.0
        business_profile_count = UserProfile.objects.filter(type = 'business').count()
        offer_count = Offer.objects.count()

        return Response({
            "review_count": review_count,
            "average_rating": average_rating,
            "business_profile_count": business_profile_count,
            "offer_count": offer_count
        }, status=status.HTTP_200_OK)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['business_user', 'reviewer'] 
    ordering_fields = ['rating', 'created_at'] 

    def get_permissions(self):
        """Apply different permissions based on the action."""
        if self.action in ['create']:
            return [IsCustomerOrAdmin()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsReviewerOrAdmin()]
        return [permissions.IsAuthenticated()]  

    def partial_update(self, request, *args, **kwargs):
        """Restrict editable fields to only 'rating' and 'description'."""
        allowed_fields = {'rating', 'description'}
        mutable_data = request.data.copy()
        request._full_data = {key: value for key, value in mutable_data.items() if key in allowed_fields}
        return super().partial_update(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        """Automatically assign the logged-in user as the reviewer."""
        serializer.save(reviewer=self.request.user)

    def get_queryset(self):
        """Allow filtering by business_user_id manually"""
        queryset = super().get_queryset()
        business_user_id = self.request.query_params.get('business_user_id')

        if business_user_id:
            queryset = queryset.filter(business_user_id=business_user_id)

        return queryset
    
    
