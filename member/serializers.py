from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Member
from agent.models import Agent

class MemberSerializer(serializers.ModelSerializer):
    """Serializer untuk Member model"""
    is_agent = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = ('id', 'username', 'email', 'phone_number', 'points', 'wallet', 'alamat', 
                  'profile_picture', 'is_oauth_user', 'latitude', 'longitude', 'address_id', 
                  'gender', 'is_agent', 'email_verified')
        read_only_fields = ('id', 'email', 'points', 'wallet', 'is_oauth_user', 
                            'latitude', 'longitude', 'address_id', 'is_agent', 'email_verified')
    
    def get_is_agent(self, obj):
        """Check if user has an agent profile"""
        return hasattr(obj, 'agent')

class MemberRegistrationSerializer(serializers.ModelSerializer):
    """Serializer untuk registrasi member baru"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    is_agent = serializers.BooleanField(required=False, default=False)
    
    class Meta:
        model = Member
        fields = ['email', 'username', 'password', 'password_confirm', 
                 'phone_number', 'alamat', 'is_agent', 'gender']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        is_agent = validated_data.pop('is_agent', False)
        
        user = Member(**validated_data)
        user.set_password(password)
        user.is_active = True  # Auto activate (no email verification)
        user.email_verified = True  # Auto verify email
        user.save()
        
        # If is_agent is True, create an Agent instance
        if is_agent:
            Agent.objects.create(
                user=user,
            )
            
        return user

class LoginSerializer(serializers.Serializer):
    """Serializer untuk login"""
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('Account is not active')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password')