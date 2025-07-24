from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat_with_ai, name='chat_with_ai'),
    path('reset/', views.reset_chat, name='reset_chat'),
    path('history/', views.get_chat_history, name='get_chat_history'),
]