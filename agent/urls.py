from django.urls import path
from . import views

urlpatterns = [
    # path('register-toko/', views.register_toko, name='register_toko'),
    # path('register/', views.register_agent, name='register_agent'),
    path('login/', views.login_agent, name='login_agent'),
    path('logout/', views.logout_agent, name='logout_agent'),

    # API endpoints (new)
    path('api/login/', views.AgentLoginAPIView.as_view(), name='api_agent_login'),
    path('api/logout/', views.AgentLogoutAPIView.as_view(), name='api_agent_logout'),
    # path('api/register/', views.AgentRegistrationAPIView.as_view(), name='api_agent_register'),
    path('api/profile/', views.AgentProfileAPIView.as_view(), name='api_agent_profile'),
] 