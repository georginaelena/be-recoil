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
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import MemberSerializer, MemberRegistrationSerializer, LoginSerializer
from .utils import generate_tokens_for_user, send_verification_email

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import json
import googlemaps
import logging
logger = logging.getLogger(__name__)

from math import radians, cos, sin, asin, sqrt
from rest_framework.decorators import api_view, permission_classes
from django.http import HttpResponseRedirect
from urllib.parse import urlencode

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
        print("tes")
        if serializer.is_valid():
            print("tesser")

            user = serializer.save()
            
            # Set default profile picture based on gender
            gender = request.data.get('gender', 'Men')
            if not user.profile_picture:
                if gender == 'Women':
                    user.profile_picture = 'https://hacks-recoil.s3.amazonaws.com/photos/female.svg'
                else:
                    user.profile_picture = 'https://hacks-recoil.s3.amazonaws.com/photos/male.svg'

            # Geocode address if present
            if user.alamat:
                try:
                    gmaps = googlemaps.Client(key=settings.GOOGLE_API_KEY)
                    geocode_result = gmaps.geocode(user.alamat)
                    logger.debug(f"Geocode result for '{user.alamat}': {geocode_result}")
                    if geocode_result:
                        location = geocode_result[0]['geometry']['location']
                        user.latitude = location['lat']
                        user.longitude = location['lng']
                        user.address_id = geocode_result[0]['place_id']
                except Exception as e:
                    # Log error but don't fail registration
                    logger.error(f"Geocoding failed: {str(e)}")

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
            
            # Check if user is an agent
            is_agent = hasattr(user, 'agent')
            
            response_data = {
                'message': 'Login successful',
                'tokens': tokens,
                'user': MemberSerializer(user).data,
                'is_agent': is_agent
            }
            
            # Add agent details if user is an agent
            if is_agent:
                response_data['agent'] = {
                    'id': user.agent.id,
                }
            
            return Response(response_data, status=status.HTTP_200_OK)
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
        user = request.user
        serializer = MemberSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            # Check if address is being updated
            if 'alamat' in request.data and request.data['alamat'] != user.alamat:
                try:
                    gmaps = googlemaps.Client(key=settings.GOOGLE_API_KEY)
                    geocode_result = gmaps.geocode(request.data['alamat'])
                    if geocode_result:
                        location = geocode_result[0]['geometry']['location']
                        serializer.validated_data['latitude'] = location['lat']
                        serializer.validated_data['longitude'] = location['lng']
                        serializer.validated_data['address_id'] = geocode_result[0]['place_id']
                    else:
                        # Handle case where address is not found
                        return Response({'error': 'Address could not be geocoded.'}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    # Log error but continue with update
                    logger.error(f"Geocoding failed during profile update: {str(e)}")

            # Set default profile picture if not provided and gender is updated
            gender = request.data.get('gender', user.gender)
            if not user.profile_picture or 'gender' in request.data:
                if gender == 'Women':
                    serializer.validated_data['profile_picture'] = 'https://hacks-recoil.s3.amazonaws.com/photos/female.svg'
                else:
                    serializer.validated_data['profile_picture'] = 'https://hacks-recoil.s3.amazonaws.com/photos/male.svg'

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
            error = request.GET.get('error')
            
            # Check if user denied access
            if error:
                error_params = {
                    'error': 'oauth_denied',
                    'message': 'Google OAuth access was denied'
                }
                error_url = f"https://fe-recoil.vercel.app/login?{urlencode(error_params)}"
                return HttpResponseRedirect(error_url)
            
            if not code:
                # Redirect to frontend with error if no code provided
                error_params = {
                    'error': 'oauth_failed',
                    'message': 'Authorization code not provided. Please try logging in again.'
                }
                error_url = f"https://fe-recoil.vercel.app/login?{urlencode(error_params)}"
                return HttpResponseRedirect(error_url)
            
            # Verify state (optional but recommended)
            session_state = request.session.get('oauth_state')
            if session_state and session_state != state:
                error_params = {
                    'error': 'oauth_failed',
                    'message': 'Invalid state parameter. Please try again.'
                }
                error_url = f"https://fe-recoil.vercel.app/login?{urlencode(error_params)}"
                return HttpResponseRedirect(error_url)
            
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
                
                # Generate JWT tokens for existing user
                tokens = generate_tokens_for_user(member)
                
                # Clean up session
                if 'oauth_state' in request.session:
                    del request.session['oauth_state']
                
                # Redirect to frontend with success and tokens
                login_params = {
                    'oauth_success': 'true',
                    'access_token': tokens['access'],
                    'refresh_token': tokens['refresh'],
                    'user_id': member.id,
                    'is_agent': 'true' if hasattr(member, 'agent') else 'false'
                }
                success_url = f"https://fe-recoil.vercel.app/login?{urlencode(login_params)}"
                return HttpResponseRedirect(success_url)
                
            except Member.DoesNotExist:
                # User doesn't exist - redirect to frontend register page
                register_params = {
                    'email': email,
                    'name': name,
                    'google_id': google_id,
                    'profile_picture': picture,
                    'oauth': 'true'
                }
                
                register_url = f"https://fe-recoil.vercel.app/register?{urlencode(register_params)}"
                
                # Clean up session
                if 'oauth_state' in request.session:
                    del request.session['oauth_state']
                
                return HttpResponseRedirect(register_url)
            
        except Exception as e:
            logger.error(f"OAuth callback error: {str(e)}")
            # Redirect to frontend with error
            error_params = {
                'error': 'oauth_failed',
                'message': f'OAuth authentication failed: {str(e)}'
            }
            error_url = f"https://fe-recoil.vercel.app/login?{urlencode(error_params)}"
            return HttpResponseRedirect(error_url)
    
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
                
                # Generate JWT tokens for existing user
                tokens = generate_tokens_for_user(member)
                
                # Clean up session
                if 'oauth_state' in request.session:
                    del request.session['oauth_state']
                
                return Response({
                    'message': f'Welcome {name}! Successfully logged in with Google.',
                    'tokens': tokens,
                    'user': MemberSerializer(member).data,
                    'is_agent': hasattr(member, 'agent')
                }, status=status.HTTP_200_OK)
                
            except Member.DoesNotExist:
                # User doesn't exist - return data for frontend to handle registration
                return Response({
                    'redirect_to_register': True,
                    'google_user_data': {
                        'email': email,
                        'name': name,
                        'google_id': google_id,
                        'profile_picture': picture
                    },
                    'register_url': 'https://fe-recoil.vercel.app/register'
                }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'OAuth authentication failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)