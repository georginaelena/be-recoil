from django.db import models
from member.models import Member
from agent.models import Agent
from item.models import Item
from agent.models import Agent

class Cart(models.Model):
    member = models.OneToOneField(Member, on_delete=models.CASCADE)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.member.email} for {self.agent.user.email}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.item} in {self.cart}"
    
class Transaction(models.Model):
    BUY = 'buy'
    SELL = 'sell'
    TRANSACTION_TYPE_CHOICES = [
        (BUY, 'Buy'),
        (SELL, 'Sell'),
    ]
    
    ONGOING = 'ongoing'
    COMPLETE = 'complete'
    STATUS_CHOICES = [
        (ONGOING, 'Ongoing'),
        (COMPLETE, 'Complete'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ONGOING)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.member.email} {self.transaction_type} {self.item} from {self.agent.user.email} - {self.status}"


class NegotiationSession(models.Model):
    agent      = models.ForeignKey(Agent,  on_delete=models.CASCADE)
    member     = models.ForeignKey(Member, on_delete=models.CASCADE)
    item       = models.ForeignKey(Item,   on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('agent','member','item')

    def __str__(self):
        return f"{self.member} ↔ {self.agent} on {self.item}"


class Offer(models.Model):
    session         = models.ForeignKey(NegotiationSession,
                                        on_delete=models.CASCADE,
                                        related_name='offers')
    price           = models.DecimalField(max_digits=12, decimal_places=2)
    quantity        = models.FloatField()
    STATUS_CHOICES  = [
        ('pending','Pending'),
        ('accepted','Accepted'),
        ('rejected','Rejected'),
        ('countered','Countered'),
    ]
    status          = models.CharField(max_length=10,
                                       choices=STATUS_CHOICES,
                                       default='pending')
    sender_is_agent = models.BooleanField()
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = "Agent" if self.sender_is_agent else "Member"
        return f"{who} offer {self.price}"


class ChatMessage(models.Model):
    session         = models.ForeignKey(NegotiationSession,
                                        on_delete=models.CASCADE,
                                        related_name='messages')
    sender_is_agent = models.BooleanField()
    content         = models.TextField()
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = "Agent" if self.sender_is_agent else "Member"
        return f"{who}: {self.content[:20]}…"
    
    
# # Update Offer model to use Item instead of Waste
# class Offer(models.Model):
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('accepted', 'Accepted'),
#         ('rejected', 'Rejected'),
#         ('countered', 'Countered'),
#     ]
    
#     member = models.ForeignKey(Member, on_delete=models.CASCADE)
#     agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
#     item = models.ForeignKey(Item, on_delete=models.CASCADE)  # Changed from waste to item
#     quantity = models.FloatField()
#     price = models.DecimalField(max_digits=12, decimal_places=2)
#     message = models.TextField(blank=True, null=True)
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
#     sender_is_agent = models.BooleanField(default=True)
#     parent_offer = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return f"Offer for {self.item.name} - {self.status}"
    
# class Message(models.Model):
    # offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='messages')
    # sender_is_agent = models.BooleanField()  # True if sent by agent, False if by member
    # content = models.TextField()
    # created_at = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     sender = "Agent" if self.sender_is_agent else "Member"
    #     return f"{sender} message for offer #{self.offer.id}"