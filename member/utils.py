from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
import uuid
from agent.models import Agent

def generate_tokens_for_user(user):
    """Generate JWT tokens untuk user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def send_verification_email(user, request):
    """Kirim email verifikasi"""
    token = uuid.uuid4().hex
    user.verification_token = token
    user.save()
    
    verification_url = request.build_absolute_uri(
        reverse('verify_member_email', args=[token])
    )
    
    send_mail(
        'Verify your email - ReCoil',
        f'Click the link to verify your email: {verification_url}',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def create_agent_for_member(member, description=''):
    """Create an agent for a member"""
    agent = Agent.objects.create(
        user=member,
    )
    return agent