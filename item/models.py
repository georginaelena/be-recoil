from django.db import models
from django.core.exceptions import ValidationError
from agent.models import Agent
from member.models import Member

class Item(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('pending', 'Pending'),
        ('sold', 'Sold'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.IntegerField()
    
    # Optional seller relationships (only one should be set)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, null=True, blank=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, null=True, blank=True)
    
    category = models.CharField(max_length=100)
    unit = models.CharField(max_length=20, default='L')
    
    # New fields for waste/item status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(null=True, blank=True)
    
    def clean(self):
        """Ensure item has exactly one seller (agent XOR member)"""
        if (self.agent and self.member) or (not self.agent and not self.member):
            raise ValidationError("Item must have exactly one seller (either agent or member).")
            
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
    def get_seller(self):
        """Return the seller (agent or member) of this item"""
        return self.agent if self.agent else self.member
    
    def __str__(self):
        seller = self.get_seller()
        seller_name = seller.username if self.member else seller.user.username
        return f"{self.name} (Sold by: {seller_name})"