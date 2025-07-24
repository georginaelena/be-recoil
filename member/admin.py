from django.contrib import admin
from .models import Member, Waste

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "username",
        "phone_number",
        "points",
        "wallet",
        "alamat",
        "latitude",
        "longitude",
        "gender",
        "email_verified",
        "is_oauth_user",
        "profile_picture",
    )
    
    list_filter = (
        "gender",
        "email_verified",
        "is_oauth_user",
        "is_active",
    )
    
    search_fields = (
        "email",
        "username",
        "phone_number",
    )
    
    readonly_fields = (
        "latitude",
        "longitude",
        "address_id",
        "verification_token",
        "google_id",
    )

@admin.register(Waste)
class WasteAdmin(admin.ModelAdmin):
    list_display = ('id', 'member_email', 'waste_type', 'quantity', 'status', 'location', 'created_at')
    list_filter = ('status', 'waste_type', 'created_at')
    search_fields = ('member__email', 'waste_type', 'description', 'location')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def member_email(self, obj):
        return obj.member.email
    member_email.short_description = 'Member'
    member_email.admin_order_field = 'member__email'
    
    # Optional: Add actions
    actions = ['mark_as_available', 'mark_as_sold']
    
    def mark_as_available(self, request, queryset):
        updated = queryset.update(status='available')
        self.message_user(request, f'{updated} wastes marked as available.')
    mark_as_available.short_description = "Mark selected wastes as available"
    
    def mark_as_sold(self, request, queryset):
        updated = queryset.update(status='sold')
        self.message_user(request, f'{updated} wastes marked as sold.')
    mark_as_sold.short_description = "Mark selected wastes as sold"
