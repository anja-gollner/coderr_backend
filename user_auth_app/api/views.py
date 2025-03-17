from rest_framework import generics
from user_auth_app.models import UserProfile
from .serializers import UserProfileSerializer, RegistrationSerializer, LoginSerializer, BusinessUserListSerializer, CustomerUserListSerializer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, NotFound




class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self):
        """
        Retrieve the UserProfile where the associated user's ID matches the URL parameter.
        """
        user_id = self.kwargs["pk"]  
        try:
            obj = UserProfile.objects.get(user__id=user_id)  
            return obj
        except UserProfile.DoesNotExist:
            raise NotFound(f"UserProfile with user_id={user_id} not found.")

    def update(self, request, *args, **kwargs):
        """ Users can only edit their own profile """
        obj = self.get_object()
        if not request.user.is_staff and obj.user != request.user:
            raise PermissionDenied("You can only edit your own profile.")
        return super().update(request, *args, **kwargs)



class BusinessUserListView(generics.ListAPIView):
    serializer_class = BusinessUserListSerializer
    permission_classes = [IsAuthenticated]  

    def get_queryset(self):
        return UserProfile.objects.filter(type='business')


class CustomerUserListView(generics.ListAPIView):
    serializer_class = CustomerUserListSerializer
    permission_classes = [IsAuthenticated]  

    def get_queryset(self):
        return UserProfile.objects.filter(type='customer')



class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            username = serializer.validated_data['username']
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            repeated_password = serializer.validated_data['repeated_password']
            type = serializer.validated_data.get('type', 'customer')  

            if password != repeated_password:
                return Response({"repeated_password": ["Die Passwörter stimmen nicht überein."]}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.create_user(username=username, email=email, password=password)
            UserProfile.objects.create(user=user, email=email, type=type, name=username)
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                "token": token.key,
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class LoginView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
