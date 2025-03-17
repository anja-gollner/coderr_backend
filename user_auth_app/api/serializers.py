from rest_framework import serializers
from user_auth_app.models import UserProfile
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.conf import settings




class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", required=False, allow_blank=True)
    last_name = serializers.CharField(source="user.last_name", required=False, allow_blank=True)
    file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = UserProfile
        fields = '__all__'

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {}) 
        file = validated_data.pop("file", None) 

        user = instance.user
        if "username" in user_data:
            user.username = user_data["username"]
        if "first_name" in user_data:
            user.first_name = user_data["first_name"]
        if "last_name" in user_data:
            user.last_name = user_data["last_name"]
        user.save()  
        if file:
            instance.file = file

        return super().update(instance, validated_data)

    
    def get_file(self, obj):
        if obj.file:
            return  f"{settings.MEDIA_URL}{obj.file}"
        return None


class RegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    repeated_password = serializers.CharField(write_only=True, required=True, min_length=6)
    type = serializers.ChoiceField(choices=UserProfile.USER_TYPES, default='customer')  

    def validate_username(self, value):
        """ Ensure the username is unique """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Dieser Benutzername ist bereits vergeben.")
        return value

    def validate_email(self, value):
        """ Ensure the email is unique """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Diese E-Mail-Adresse wird bereits verwendet.")
        return value

    def validate(self, data):
        """ Ensure passwords match """
        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError({"repeated_password": "Die Passwörter stimmen nicht überein."})
        return data
       

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            raise serializers.ValidationError({"detail": ["Benutzername und Passwort sind erforderlich."]})

        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError({"detail": ["Ungültige Anmeldeinformationen."]})

        token, created = Token.objects.get_or_create(user=user)

        return {
            "token": token.key,
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        }
    

class BusinessUserListSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['user', 'file', 'location', 'tel', 'description', 'working_hours', 'type']

    def get_user(self, obj):
        """Returns nested user details as required in the response."""
        return {
            "pk": obj.user.pk,
            "username": obj.user.username,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name
        }

    def get_file(self, obj):
        """Ensure file URL includes MEDIA_URL."""
        if obj.file:
            return f"{settings.MEDIA_URL}{obj.file}"  
        return None  
    
    
class CustomerUserListSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()
    uploaded_at = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['user', 'file', 'location', 'tel', 'description', 'uploaded_at', 'type']

    def get_user(self, obj):
        """Returns nested user details."""
        return {
            "pk": obj.user.pk,
            "username": obj.user.username,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name
        }

    def get_file(self, obj):
        """Ensure file URL includes MEDIA_URL."""
        if obj.file:
            return f"{settings.MEDIA_URL}{obj.file}"  
        return None
    
    def get_uploaded_at(self,obj):
        return obj.created_at