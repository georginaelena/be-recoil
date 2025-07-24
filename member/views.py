from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Member
from django.views.decorators.csrf import csrf_exempt
import uuid
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import MemberSerializer, MemberRegistrationSerializer, LoginSerializer
from .utils import generate_tokens_for_user, send_verification_email

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import json

# Create your views here.

@csrf_exempt
def register_member(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        phone_number = request.POST.get('phone_number')
        alamat = request.POST.get('alamat')
        
        if Member.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'register_member.html')
        
        # Create member without email verification
        member = Member(
            email=email, 
            username=username, 
            phone_number=phone_number, 
            alamat=alamat, 
            is_active=True,  # Directly activate the user
            email_verified=True  # Mark email as verified
        )
        member.set_password(password)
        member.save()
        
        messages.success(request, 'Registration successful! You can now login.')
        return redirect('login_member')
        messages.success(request, 'Registration successful. Please check your email to verify your account.')
        return redirect('login_member')
    return render(request, 'register_member.html')

def verify_member_email(request, token):
    try:
        member = Member.objects.get(verification_token=token)
        member.is_active = True
        member.email_verified = True
        member.verification_token = ''
        member.save()
        messages.success(request, 'Email verified! You can now login.')
    except Member.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link.')
    return redirect('login_member')

@csrf_exempt
def login_member(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            if not user.is_active or not user.email_verified:
                messages.error(request, 'Please verify your email before logging in.')
                return redirect('login_member')
            login(request, user)
            return redirect('home')  # Always redirect to home
        else:
            messages.error(request, 'Invalid email or password')
            return redirect('login_member')
    return render(request, 'member/login_member.html')

@login_required
def logout_member(request):
    logout(request)
    return redirect('login_member')

def choose_role(request):
    return render(request, 'choose_role.html')

class RegisterAPIView(APIView):
    """API untuk registrasi member baru"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = MemberRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Automatically activate user (no email verification needed)
            user.is_active = True
            user.email_verified = True
            user.save()
            
            # Check if user was registered as an agent
            is_agent = request.data.get('is_agent', False)
            response_data = {
                'message': 'Registration successful. Account is now active.',
                'user': MemberSerializer(user).data
            }
            
            # Add agent details to response if registered as agent
            if is_agent and hasattr(user, 'agent'):
                response_data['agent'] = {
                    'id': user.agent.id,
                }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(APIView):
    """API untuk login member"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = generate_tokens_for_user(user)
            return Response({
                'message': 'Login successful',
                'tokens': tokens,
                'user': MemberSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutAPIView(APIView):
    """API untuk logout member"""
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)

class ProfileAPIView(APIView):
    """API untuk mendapatkan dan update profile user"""
    
    def get(self, request):
        serializer = MemberSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = MemberSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailAPIView(APIView):
    """API untuk email verification"""
    permission_classes = [AllowAny]
    
    def post(self, request, token):
        try:
            member = Member.objects.get(verification_token=token)
            member.is_active = True
            member.email_verified = True
            member.verification_token = ''
            member.save()
            return Response({
                'message': 'Email verified successfully!'
            }, status=status.HTTP_200_OK)
        except Member.DoesNotExist:
            return Response({
                'error': 'Invalid or expired verification token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
class GoogleOAuthLoginAPIView(APIView):
    """API untuk redirect ke Google OAuth"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                        "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [settings.GOOGLE_OAUTH2_REDIRECT_URI]
                    }
                },
                scopes=['https://www.googleapis.com/auth/userinfo.email', 
                        'https://www.googleapis.com/auth/userinfo.profile', 
                        'openid']
            )
            flow.redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            # Store state in session for security
            request.session['oauth_state'] = state
            
            return Response({
                'authorization_url': authorization_url,
                'state': state
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'OAuth configuration error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GoogleOAuthCallbackAPIView(APIView):
    """API untuk handle Google OAuth callback"""
    permission_classes = [AllowAny]

    def get(self, request):
        """Handle GET request dari Google OAuth redirect"""
        try:
            # Get authorization code from URL parameters
            code = request.GET.get('code')
            state = request.GET.get('state')
            
            if not code:
                return Response({
                    'error': 'Authorization code not provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify state (optional but recommended)
            session_state = request.session.get('oauth_state')
            if session_state and session_state != state:
                return Response({
                    'error': 'Invalid state parameter'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Exchange code for token
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                        "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [settings.GOOGLE_OAUTH2_REDIRECT_URI]
                    }
                },
                scopes=['https://www.googleapis.com/auth/userinfo.email', 
                        'https://www.googleapis.com/auth/userinfo.profile', 
                        'openid']
            )
            flow.redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
            flow.fetch_token(code=code)
            
            # Get user info from Google
            credentials = flow.credentials
            request_session = google_requests.Request()
            idinfo = id_token.verify_oauth2_token(
                credentials.id_token, request_session, settings.GOOGLE_OAUTH2_CLIENT_ID
            )
            
            google_id = idinfo['sub']
            email = idinfo['email']
            name = idinfo.get('name', '')
            picture = idinfo.get('picture', '')
            
            # Check if user exists
            try:
                member = Member.objects.get(email=email)
                if not member.google_id:
                    # Link existing account with Google
                    member.google_id = google_id
                    member.profile_picture = picture
                    member.is_oauth_user = True
                    member.email_verified = True  # Google emails are pre-verified
                    member.is_active = True
                    member.save()
            except Member.DoesNotExist:
                # Create new user
                username = email.split('@')[0]  # Use email prefix as username
                counter = 1
                original_username = username
                
                # Ensure unique username
                while Member.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                member = Member(
                    email=email,
                    username=username,
                    google_id=google_id,
                    profile_picture=picture,
                    is_oauth_user=True,
                    email_verified=True,
                    is_active=True
                )
                # Set unusable password for OAuth users
                member.set_unusable_password()
                member.save()
            
            # Generate JWT tokens
            tokens = generate_tokens_for_user(member)
            
            # Clean up session
            if 'oauth_state' in request.session:
                del request.session['oauth_state']
            
            return Response({
                'message': f'Welcome {name}! Successfully logged in with Google.',
                'tokens': tokens,
                'user': MemberSerializer(member).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'OAuth authentication failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request):
        try:
            # Get authorization code from request
            code = request.data.get('code')
            state = request.data.get('state')
            
            if not code:
                return Response({
                    'error': 'Authorization code not provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify state (optional but recommended)
            session_state = request.session.get('oauth_state')
            if session_state and session_state != state:
                return Response({
                    'error': 'Invalid state parameter'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Exchange code for token
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                        "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [settings.GOOGLE_OAUTH2_REDIRECT_URI]
                    }
                },
                scopes=['https://www.googleapis.com/auth/userinfo.email', 
                        'https://www.googleapis.com/auth/userinfo.profile', 
                        'openid']
            )
            flow.redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
            flow.fetch_token(code=code)
            
            # Get user info from Google
            credentials = flow.credentials
            request_session = google_requests.Request()
            idinfo = id_token.verify_oauth2_token(
                credentials.id_token, request_session, settings.GOOGLE_OAUTH2_CLIENT_ID
            )
            
            google_id = idinfo['sub']
            email = idinfo['email']
            name = idinfo.get('name', '')
            picture = idinfo.get('picture', '')
            
            # Check if user exists
            try:
                member = Member.objects.get(email=email)
                if not member.google_id:
                    # Link existing account with Google
                    member.google_id = google_id
                    member.profile_picture = picture
                    member.is_oauth_user = True
                    member.email_verified = True  # Google emails are pre-verified
                    member.is_active = True
                    member.save()
            except Member.DoesNotExist:
                # Create new user
                username = email.split('@')[0]  # Use email prefix as username
                counter = 1
                original_username = username
                
                # Ensure unique username
                while Member.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                member = Member(
                    email=email,
                    username=username,
                    google_id=google_id,
                    profile_picture=picture,
                    is_oauth_user=True,
                    email_verified=True,
                    is_active=True
                )
                # Set unusable password for OAuth users
                member.set_unusable_password()
                member.save()
            
            # Generate JWT tokens
            tokens = generate_tokens_for_user(member)
            
            # Clean up session
            if 'oauth_state' in request.session:
                del request.session['oauth_state']
            
            return Response({
                'message': f'Welcome {name}! Successfully logged in with Google.',
                'tokens': tokens,
                'user': MemberSerializer(member).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'OAuth authentication failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)