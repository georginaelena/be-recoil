from django.db import models
from django.conf import settings
from member.models import Member

class ChatSession(models.Model):
    user = models.ForeignKey(Member, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Chat session {self.session_id} for {self.user.username}"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    is_user = models.BooleanField()  # True if sent by user, False if from AI
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    item_id = models.IntegerField(null=True, blank=True)  # Store the item_id reference
    
    def __str__(self):
        sender = "User" if self.is_user else "AI"
        return f"{sender} message in {self.session}"

class TokenUsage(models.Model):
    user = models.ForeignKey(Member, on_delete=models.CASCADE)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.total_tokens} tokens"