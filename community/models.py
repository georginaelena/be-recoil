from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Blog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blogs')
    date_added = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    body = models.TextField()
    image = models.ImageField(null=True, blank=True)


    def __str__(self):
        return self.title

class BlogThumbsUp(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='thumbs_ups')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_thumbs_ups')
    date_given = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blog', 'user')

    def __str__(self):
        return f"{self.user.username} thumbs up {self.blog.title}"

# QnA Models
class Question(models.Model):
    CATEGORY_CHOICES = [
        ('kualitas limbah', 'Kualitas Limbah'),
        ('harga limbah', 'Harga Limbah'),
        ('recoil', 'Recoil'),
        ('lainnya', 'Lainnya'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    date_added = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    body = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')

    def __str__(self):
        return self.title

class Comment(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    date_added = models.DateTimeField(auto_now_add=True)
    body = models.TextField()

    def __str__(self):
        return f"Comment by {self.user.username} on {self.question.title}"

class CommentThumbsUp(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='thumbs_ups')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_thumbs_ups')
    date_given = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'user')

    def __str__(self):
        return f"{self.user.username} thumbs up comment {self.comment.id}"
