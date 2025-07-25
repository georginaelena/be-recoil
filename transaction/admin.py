from django.contrib import admin
from .models import Cart, CartItem, Transaction, Offer

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'member', 'agent', 'created_at']
    list_filter = ['created_at']
    search_fields = ['member__username', 'agent__user__username']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'item', 'quantity']
    list_filter = ['cart__created_at']
    search_fields = ['cart__member__username', 'item__name']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'member', 'agent', 'item', 'transaction_type', 'quantity', 'total_price', 'status', 'created_at']
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['member__username', 'agent__user__username', 'item__name']
    readonly_fields = ['created_at', 'completed_at']

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_member', 'get_agent', 'get_item', 'price', 'status', 'sender_is_agent', 'created_at']
    list_filter = ['status', 'sender_is_agent', 'created_at']
    search_fields = ['member__username', 'agent__user__username', 'item__name']
    readonly_fields = ['created_at']
    
    def get_member(self, obj):
        return obj.member.username if obj.member else 'N/A'
    get_member.short_description = 'Member'
    
    def get_agent(self, obj):
        return obj.agent.user.username if obj.agent else 'N/A'
    get_agent.short_description = 'Agent'
    
    def get_item(self, obj):
        return obj.item.name if obj.item else 'N/A'
    get_item.short_description = 'Item'