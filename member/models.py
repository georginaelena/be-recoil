from django.db import models
from django.contrib.auth.models import AbstractUser

class Member(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    points = models.IntegerField(default=0)
    wallet = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00)
    alamat = models.TextField(blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=64, blank=True, null=True)
    address_id = models.CharField(max_length=255, blank=True, null=True)
    
    GENDER_CHOICES = [
        ('Men', 'Men'), 
        ('Women', 'Women'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Men')

    #OAuth
    google_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    profile_picture = models.URLField(blank=True, null=True)
    is_oauth_user = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class Waste(models.Model):
    WASTE_TYPE_CHOICES = [
        ('motor oil', 'Motor Oil'),
        ('cooking oil', 'Cooking Oil'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('pending', 'Pending'),
        ('sold', 'Sold'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    waste_type = models.CharField(max_length=20, choices=WASTE_TYPE_CHOICES)
    quantity = models.FloatField()   
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.member.email} - {self.waste_type} - {self.quantity}L'
