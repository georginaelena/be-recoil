from django.db import models
from member.models import Member

class Agent(models.Model):
    user = models.OneToOneField(Member, on_delete=models.CASCADE)
    is_ekspedisi = models.BooleanField(default=False)
    description = models.TextField()
    rating = models.FloatField(default=0.0)


    def __str__(self):
        return self.user.email
