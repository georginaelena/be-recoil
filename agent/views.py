from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from member.models import Member
from .models import Agent
from django.views.decorators.csrf import csrf_exempt

# REST Framework imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from member.utils import generate_tokens_for_user
from member.serializers import MemberSerializer

# Create your views here.

@csrf_exempt
# def register_toko(request):
#     if request.method == 'POST':
#         store_name = request.POST.get('store_name')
#         description = request.POST.get('description')
#         alamat = request.POST.get('alamat')
#         if not store_name or not description or not alamat:
#             messages.error(request, 'All fields are required.')
#             return render(request, 'agent/register_toko.html')
#         toko = Toko.objects.create(store_name=store_name, description=description, alamat=alamat, rating=0.0)
#         request.session['new_toko_id'] = toko.id
#         return redirect('register_agent')
#     return render(request, 'agent/register_toko.html')

# @csrf_exempt
# def register_agent(request):
#     toko_id = request.session.get('new_toko_id')
#     if not toko_id:
#         return redirect('register_toko')
#     try:
#         toko = Toko.objects.get(id=toko_id)
#     except Toko.DoesNotExist:
#         messages.error(request, 'Store not found. Please register the store first.')
#         return redirect('register_toko')
#     if request.method == 'POST':
#         email = request.POST.get('email')
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         phone_number = request.POST.get('phone_number')
#         alamat = request.POST.get('alamat')
#         is_ekspedisi = request.POST.get('is_ekspedisi') == 'True' or request.POST.get('is_ekspedisi') == 'on'
#         if Member.objects.filter(email=email).exists():
#             messages.error(request, 'Email already registered')
#             return render(request, 'agent/register_agent.html', {'toko': toko})
#         member = Member(email=email, username=username, phone_number=phone_number, alamat=alamat)
#         member.set_password(password)
#         member.save()
#         agent = Agent(user=member, store=toko, is_ekspedisi=is_ekspedisi, alamat=alamat)
#         agent.save()
#         del request.session['new_toko_id']
#         messages.success(request, 'Agent registration successful. Please login.')
#         return redirect('login_agent')
#     return render(request, 'agent/register_agent.html', {'toko': toko})

@csrf_exempt
def login_agent(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None and hasattr(user, 'agent'):
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid email, password, or not an agent')
            return render(request, 'agent/login_agent.html')
    return render(request, 'agent/login_agent.html')

@login_required
def logout_agent(request):
    logout(request)
    return redirect('login_agent')

# REST API views (new)
class AgentLoginAPIView(APIView):
    """API for agent login"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        print(f"API login attempt for email: {email}")

        user = authenticate(email=email, password=password)
        print(f"Authentication result: {user}")
        if user:
            print(f"Has agent attribute: {hasattr(user, 'agent')}")
            print(f"User type: {type(user)}")
        
        
        if user is not None and hasattr(user, 'agent'):
            tokens = generate_tokens_for_user(user)
            return Response({
                'status': 'success',
                'message': 'Login successful',
                'tokens': tokens,
                'user': MemberSerializer(user).data,
                'agent': {
                    'id': user.agent.id,
                    'is_ekspedisi': user.agent.is_ekspedisi,
                    'description': user.agent.description,
                    'rating': user.agent.rating
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error', 
                'message': 'Invalid email, password, or not an agent'
            }, status=status.HTTP_401_UNAUTHORIZED)

class AgentLogoutAPIView(APIView):
    """API for agent logout"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                'status': 'success',
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Invalid token: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

# class AgentRegistrationAPIView(APIView):
#     """API for agent registration"""
#     permission_classes = [AllowAny]
    
#     def post(self, request):
#         try:
#             # Store data
#             store_name = request.data.get('store_name')
#             store_description = request.data.get('store_description')
#             store_alamat = request.data.get('store_alamat')
            
#             # Agent user data
#             email = request.data.get('email')
#             username = request.data.get('username')
#             password = request.data.get('password')
#             phone_number = request.data.get('phone_number')
#             alamat = request.data.get('alamat')
#             is_ekspedisi = request.data.get('is_ekspedisi', False)
#             description = request.data.get('description', 'New agent')
            
#             # Validation
#             if not store_name or not store_description or not email or not username or not password:
#                 return Response({
#                     'status': 'error',
#                     'message': 'Missing required fields'
#                 }, status=status.HTTP_400_BAD_REQUEST)
                
#             # Check if email exists
#             if Member.objects.filter(email=email).exists():
#                 return Response({
#                     'status': 'error',
#                     'message': 'Email already registered'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Create store (toko)
#             toko = Toko.objects.create(
#                 store_name=store_name,
#                 description=store_description,
#                 alamat=store_alamat,
#                 rating=0.0
#             )
            
#             # Create member user
#             member = Member(
#                 email=email,
#                 username=username,
#                 phone_number=phone_number,
#                 alamat=alamat,
#                 email_verified=True,  # Assuming agent emails are pre-verified
#                 is_active=True
#             )
#             member.set_password(password)
#             member.save()
            
#             # Create agent
#             agent = Agent(
#                 user=member,
#                 is_ekspedisi=is_ekspedisi,
#                 description=description
#             )
#             agent.save()
            
#             # Generate tokens for the new agent
#             tokens = generate_tokens_for_user(member)
            
#             return Response({
#                 'status': 'success',
#                 'message': 'Agent registration successful',
#                 'tokens': tokens,
#                 'user': MemberSerializer(member).data,
#                 'agent': {
#                     'id': agent.id,
#                     'is_ekspedisi': agent.is_ekspedisi,
#                     'description': agent.description,
#                     'rating': agent.rating
#                 }
#             }, status=status.HTTP_201_CREATED)
            
#         except Exception as e:
#             return Response({
#                 'status': 'error',
#                 'message': f'Registration failed: {str(e)}'
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AgentProfileAPIView(APIView):
    """API for getting and updating agent profile"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'agent'):
            return Response({
                'status': 'error',
                'message': 'User is not an agent'
            }, status=status.HTTP_403_FORBIDDEN)
            
        agent = user.agent
        
        return Response({
            'status': 'success',
            'user': MemberSerializer(user).data,
            'agent': {
                'id': agent.id,
                'is_ekspedisi': agent.is_ekspedisi,
                'description': agent.description,
                'rating': agent.rating
            }
        }, status=status.HTTP_200_OK)
        
    def put(self, request):
        user = request.user
        
        if not hasattr(user, 'agent'):
            return Response({
                'status': 'error',
                'message': 'User is not an agent'
            }, status=status.HTTP_403_FORBIDDEN)
            
        agent = user.agent
        
        # Update agent fields
        if 'description' in request.data:
            agent.description = request.data['description']
        
        if 'is_ekspedisi' in request.data:
            agent.is_ekspedisi = request.data['is_ekspedisi']
        
        agent.save()
        
        # Update user fields if provided
        user_updated = False
        if 'username' in request.data:
            user.username = request.data['username']
            user_updated = True
            
        if 'phone_number' in request.data:
            user.phone_number = request.data['phone_number']
            user_updated = True
            
        if 'alamat' in request.data:
            user.alamat = request.data['alamat']
            user_updated = True
            
        if user_updated:
            user.save()
        
        return Response({
            'status': 'success',
            'message': 'Profile updated successfully',
            'user': MemberSerializer(user).data,
            'agent': {
                'id': agent.id,
                'is_ekspedisi': agent.is_ekspedisi,
                'description': agent.description,
                'rating': agent.rating
            }
        }, status=status.HTTP_200_OK)