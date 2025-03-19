from rest_framework import viewsets, filters, status, permissions
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from coderr_app.models import Offer, OfferDetails, Order, Review
from user_auth_app.models import UserProfile
from .serializers import OfferSerializer, OfferDetailsSerializer, OrderSerializer, CreateOrderSerializer, UpdateOrderStatusSerializer, ReviewSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import IsBusinessOwnerOrAdmin, IsCustomerOrAdmin, IsReviewerOrAdmin
from .pagination import CustomPageNumberPagination  
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Avg
from django.db.models import Min, Q
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class OfferViewset(viewsets.ModelViewSet):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    permission_classes = [AllowAny]
    pagination_class = CustomPageNumberPagination

    filterset_fields = {
        'user': ['exact'], 
        'updated_at': ['gte'],
        'offer_details__price': ['gte'],  
        'offer_details__delivery_time_in_days': ['exact', 'lte', 'gte']
    }
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at']

    def get_queryset(self):
        queryset = Offer.objects.annotate(
            min_price=Min('offer_details__price')
        )
        creator_id = self.request.query_params.get('creator_id')
        max_delivery_time = self.request.query_params.get('max_delivery_time')
        min_price = self.request.query_params.get('min_price')

        if creator_id:
            queryset = queryset.filter(user_id=creator_id)

        if max_delivery_time:
            try:
                max_delivery_time = int(max_delivery_time)
            except ValueError:
                raise ValidationError({"error": "max_delivery_time muss eine Ganzzahl sein."})
            queryset = queryset.filter(offer_details__delivery_time_in_days__lte=max_delivery_time)

        if min_price:
            try:
                min_price = float(min_price)
            except ValueError:
                raise ValidationError({"error": "min_price muss eine Zahl sein."})
            queryset = queryset.filter(min_price__gte=min_price)

        return queryset



    def retrieve(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            raise AuthenticationFailed({"detail": "Authentifizierung erforderlich."})
        instance = get_object_or_404(Offer, pk=kwargs.get("pk"))
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise AuthenticationFailed({"detail": "Authentifizierung erforderlich."}) #401
        user_profile = getattr(self.request.user, "profile", None)
        if not user_profile or user_profile.type != "business":
            raise PermissionDenied({"detail": "Nur Business-Nutzer dürfen Angebote erstellen."}) #403
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        if not self.request.user.is_authenticated:
            raise AuthenticationFailed({"detail": "Authentifizierung erforderlich."})  # 401
        if instance.user != self.request.user:
            raise PermissionDenied({"detail": "Du hast keine Berechtigung, dieses Angebot zu bearbeiten."})  # 403
        user_profile = getattr(self.request.user, "profile", None)
        if not user_profile or user_profile.type != "business":
            raise PermissionDenied({"detail": "Nur Business-Nutzer dürfen ihre Angebote bearbeiten."})  # 403
        serializer.save()

    def handle_exception(self, exc):
        response = super().handle_exception(exc)
        if response is None:
            return Response({"detail": "Interner Serverfehler"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return response
        

class OfferDetailsViewSet(viewsets.ModelViewSet):
    queryset = OfferDetails.objects.all()
    serializer_class = OfferDetailsSerializer

    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"detail": "Benutzer ist nicht authentifiziert."}, status=status.HTTP_401_UNAUTHORIZED)  # 401
        pk = kwargs.get("pk")
        if pk is None or not str(pk).isdigit():  
            return Response({"detail": "Ungültige oder fehlende ID."}, status=status.HTTP_400_BAD_REQUEST)  # 400
        offer_detail = get_object_or_404(OfferDetails, pk=kwargs.get("pk"))
        serializer = self.get_serializer(offer_detail)
        return Response(serializer.data, status=status.HTTP_200_OK)  # 200 OK

    def handle_exception(self, exc):
        response = super().handle_exception(exc)
        if response is None:
            return Response({"detail": "Interner Serverfehler"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  # 500
        return response


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

    def create(self, request, *args, **kwargs):
        """Erstelle eine Bestellung und sende die richtigen Statuscodes zurück."""
        if not request.user.is_authenticated:
            return Response({"detail": "Benutzer ist nicht authentifiziert."}, status=status.HTTP_401_UNAUTHORIZED)  # 401
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                order = serializer.save()
                return Response(
                    serializer.to_representation(order), 
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response({"detail": "Interner Serverfehler"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  # 500
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # 400
        

    def partial_update(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentifizierung erforderlich."}, status=status.HTTP_401_UNAUTHORIZED)
        user_profile = getattr(request.user, 'profile', None)
        if not user_profile or user_profile.type != 'business':
            return Response({"detail": "Nur Business-Nutzer dürfen den Status einer Bestellung aktualisieren."}, status=status.HTTP_403_FORBIDDEN)
        order = self.get_object()
        if not order:
            return Response({"detail": "Die angegebene Bestellung wurde nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(order, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": "Interner Serverfehler."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def handle_exception(self, exc):
        response = super().handle_exception(exc)
        if response is None:
            return Response({"detail": "Interner Serverfehler"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  # 500
        return response
    
class OrderCountView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, business_user_id): 
        business_user = get_object_or_404(User, id=business_user_id)
        order_count = Order.objects.filter(business_user=business_user, status='in_progress').count()
        return Response({"order_count": order_count}, status=status.HTTP_200_OK)
    
class CompletedOrderCountView(APIView):
    permission_classes = [IsAuthenticated]
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
    ordering_fields = ['rating', 'updated_at'] 

    def get_permissions(self):
        if self.action in ['create']:
            return [IsCustomerOrAdmin()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsReviewerOrAdmin()]
        return [permissions.IsAuthenticated()]  

    def partial_update(self, request, *args, **kwargs):
        allowed_fields = {'rating', 'description'}
        mutable_data = request.data.copy()
        request._full_data = {key: value for key, value in mutable_data.items() if key in allowed_fields}
        return super().partial_update(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        business_user = serializer.validated_data['business_user']
        if Review.objects.filter(reviewer=self.request.user, business_user=business_user).exists():
            raise serializers.ValidationError({"detail": "Du hast bereits eine Bewertung für diesen Geschäftsbenutzer abgegeben."})
        serializer.save(reviewer=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        business_user_id = self.request.query_params.get('business_user_id')
        reviewer_id = self.request.query_params.get('reviewer_id')

        if business_user_id:
            queryset = queryset.filter(business_user_id=business_user_id)
        if reviewer_id:
            queryset = queryset.filter(reviewer_id=reviewer_id)
        return queryset
    
    
    
