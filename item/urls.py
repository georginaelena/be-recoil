from django.urls import path
from . import views

urlpatterns = [
    # Item details
    path('<int:item_id>/', views.item_detail, name='item_detail'),
    
    # CRUD operations
    path('add/', views.add_item, name='add_item'),
    path('<int:item_id>/update/', views.update_item, name='update_item'),
    path('<int:item_id>/delete/', views.delete_item, name='delete_item'),
    
    # User's own items
    path('my/', views.my_items, name='my_items'),
    
    # Marketplace items (members see agent items, agents see member items)
    path('all/', views.get_all_items, name='marketplace_items'),
]