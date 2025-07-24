from django.urls import path
from . import views
from .location_views import nearest_members
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', views.register_member, name='register_member'),
    path('login/', views.login_member, name='login_member'),
    path('logout/', views.logout_member, name='logout_member'),
    path('verify/<str:token>/', views.verify_member_email, name='verify_member_email'),
    path('choose-role/', views.choose_role, name='choose_role'),

        # API URLs baru
    path('api/register/', views.RegisterAPIView.as_view(), name='api_register'),
    path('api/login/', views.LoginAPIView.as_view(), name='api_login'),
    path('api/logout/', views.LogoutAPIView.as_view(), name='api_logout'),
    path('api/profile/', views.ProfileAPIView.as_view(), name='api_profile'),
    path('api/verify/<str:token>/', views.VerifyEmailAPIView.as_view(), name='api_verify_email'),

    # OAuth URLs
    path('api/oauth/google/', views.GoogleOAuthLoginAPIView.as_view(), name='api_oauth_google'),
    path('api/oauth/google/callback/', views.GoogleOAuthCallbackAPIView.as_view(), name='api_oauth_google_callback'),
    
    # Location-based URLs
    path('api/nearest-members/', nearest_members, name='nearest_members'),
    
    # JWT token endpoints
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] 