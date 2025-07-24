from django.contrib import admin
from .models import ChatSession, ChatMessage, TokenUsage

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ['is_user', 'content', 'created_at', 'item_id']
    can_delete = False

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'created_at']
    search_fields = ['session_id', 'user__username', 'user__email']
    readonly_fields = ['session_id', 'user', 'created_at']
    inlines = [ChatMessageInline]
    
    def has_add_permission(self, request):
        return False

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['get_session_id', 'get_user', 'is_user', 'short_content', 'item_id', 'created_at']
    list_filter = ['is_user', 'created_at', 'item_id']
    search_fields = ['content', 'session__session_id', 'session__user__username', 'item_id']
    readonly_fields = ['session', 'is_user', 'content', 'item_id', 'created_at']
    
    def get_session_id(self, obj):
        return obj.session.session_id
    get_session_id.short_description = 'Session ID'
    
    def get_user(self, obj):
        return obj.session.user.username
    get_user.short_description = 'User'
    
    def short_content(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'
    
    def has_add_permission(self, request):
        return False

@admin.register(TokenUsage)
class TokenUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_tokens', 'prompt_tokens', 'completion_tokens', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['user', 'prompt_tokens', 'completion_tokens', 'total_tokens', 'created_at']
    
    def has_add_permission(self, request):
        return False