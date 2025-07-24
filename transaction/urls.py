from django.urls import path
from . import views

urlpatterns = [
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/edit_quantity/', views.edit_cart_item_quantity, name='edit_cart_item_quantity'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('checkout/', views.checkout, name='checkout'),

    path('history/', views.get_transaction_history, name='get_transaction_history'),
    path('<int:transaction_id>/complete/', views.complete_transaction, name='complete_transaction'),

    path('offers/create/', views.create_offer, name='create_offer'),
    path('offers/<int:offer_id>/respond/', views.respond_to_offer, name='respond_to_offer'),
    path('offers/<int:offer_id>/messages/send/', views.send_message, name='send_message'),
    path('offers/<int:offer_id>/get-offer-with-messages/', views.get_offer_with_messages, name='get_offer_with_messages'),

    path('offers/latest-accepted/member/<int:member_id>/', views.get_latest_accepted_offer, name='get_latest_accepted_offer_for_member'),
    path('offers/latest-accepted/agent/<int:agent_id>/', views.get_latest_accepted_offer, name='get_latest_accepted_offer_for_agent'),
]