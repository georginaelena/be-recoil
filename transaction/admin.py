from django.contrib import admin
from .models import Cart, CartItem, Transaction, Offer,Message

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id","member", "created_at")

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id","cart", "item", "quantity")

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "member",
        "agent",
        "item",
        "transaction_type",
        "quantity",
        "total_price",
        "created_at",
    )

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "member",
        "agent",
        "item",
        "quantity",
        "price",
        "status",
        "sender_is_agent",
        "created_at",
    )
    list_filter = ("status", "sender_is_agent", "created_at")
    search_fields = ("member__email", "agent__user__email", "item__name")

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "offer",
        "sender_is_agent",
        "content",
        "created_at",
    )
    list_filter = ("sender_is_agent", "created_at")
    search_fields = ("content", "offer__id")