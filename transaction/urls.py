from django.urls import path
from . import views

urlpatterns = [
    # Cart management
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/view/', views.view_cart, name='view_cart'),
    path('cart/edit/', views.edit_cart_item_quantity, name='edit_cart_item_quantity'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Checkout and transactions
    path('checkout/', views.checkout, name='checkout'),
    path('history/', views.get_transaction_history, name='get_transaction_history'),
    path('<int:transaction_id>/complete/', views.complete_transaction, name='complete_transaction'),
    
    # Negotiation sessions
    path('sessions/create/', views.create_or_get_session, name='create_or_get_session'),
    path('sessions/', views.list_sessions, name='list_sessions'),
    path('sessions/<int:session_id>/', views.session_detail, name='session_detail'),
]