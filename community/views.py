from django.shortcuts import render
from django.http import JsonResponse
from .models import Blog, BlogThumbsUp
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes
from django.conf import settings
import logging
import os
from storages.backends.s3boto3 import S3Boto3Storage
from django.core.files.base import ContentFile
from django.db import transaction


# Create your views here.

@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_all_blogs(request):
    blogs = Blog.objects.all().order_by('-date_added')
    data = [
        {
            'id': blog.id,
            'username': blog.user.username,
            'date_added': blog.date_added,
            'title': blog.title,
            'body': blog.body,
            'thumbs_up_count': blog.thumbs_ups.count(),
            'image_url': blog.image.url if blog.image else None,
        }
        for blog in blogs
    ]
    return JsonResponse({'blogs': data})

@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_blog_details(request, blog_id):
    try:
        blog = Blog.objects.get(id=blog_id)
        data = {
            'id': blog.id,
            'username': blog.user.username,
            'date_added': blog.date_added,
            'title': blog.title,
            'body': blog.body,
            'thumbs_up_count': blog.thumbs_ups.count(),
            'image_url': blog.image.url if blog.image else None,
        }
        return JsonResponse({'blog': data})
    except Blog.DoesNotExist:
        return JsonResponse({'error': 'Blog not found.'}, status=404)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def get_my_blogs(request):
    blogs = Blog.objects.filter(user=request.user).order_by('-date_added')
    data = [
        {
            'id': blog.id,
            'username': blog.user.username,
            'date_added': blog.date_added,
            'title': blog.title,
            'body': blog.body,
            'thumbs_up_count': blog.thumbs_ups.count(),
        }
        for blog in blogs
    ]
    return JsonResponse({'blogs': data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
@parser_classes([MultiPartParser, FormParser])
@transaction.atomic
def create_blog(request):
    title = request.data.get('title')
    body  = request.data.get('body')
    image = request.FILES.get('image')

    if not title or not body:
        return JsonResponse({'error': 'Title and body are required.'}, status=400)

    blog = Blog(user=request.user, title=title, body=body)

    if image:
        storage = S3Boto3Storage()
        key = f"photos/{image.name}"
        saved_name = storage.save(key, image)
        blog.image.name = saved_name

    blog.save()

    return JsonResponse({'message': 'Blog created successfully.', 'blog_id': blog.id})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
@parser_classes([MultiPartParser, FormParser])
@transaction.atomic
def edit_blog(request, blog_id):
    try:
        blog = Blog.objects.get(id=blog_id, user=request.user)
    except Blog.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    title = request.data.get('title')
    body  = request.data.get('body')
    image = request.FILES.get('image')

    if title:
        blog.title = title
    if body:
        blog.body  = body
    if image:
        storage = S3Boto3Storage()
        key = f"photos/{image.name}"
        saved_name = storage.save(key, image)
        blog.image.name = saved_name

    blog.save()
    return JsonResponse({'message': 'Blog updated successfully.'})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def delete_blog(request, blog_id):
    if request.method == 'DELETE':
        try:
            blog = Blog.objects.get(id=blog_id, user=request.user)
            blog.delete()
            return JsonResponse({'message': 'Blog deleted successfully.'})
        except Blog.DoesNotExist:
            return JsonResponse({'error': 'Blog not found or not owned by user.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def thumbs_up_blog(request, blog_id):
    try:
        blog = Blog.objects.get(id=blog_id)
        
        # Check if user already gave thumbs up
        existing_thumbs_up = BlogThumbsUp.objects.filter(blog=blog, user=request.user).first()
        
        if existing_thumbs_up:
            # User already liked, so unlike (remove thumbs up)
            existing_thumbs_up.delete()
            action = 'unliked'
        else:
            # User hasn't liked yet, so like (add thumbs up)
            BlogThumbsUp.objects.create(blog=blog, user=request.user)
            action = 'liked'
        
        # Get updated thumbs up count
        thumbs_up_count = blog.thumbs_ups.count()
        
        return JsonResponse({
            'message': f'Blog {action} successfully.',
            'action': action,
            'thumbs_up_count': thumbs_up_count
        })
        
    except Blog.DoesNotExist:
        return JsonResponse({'error': 'Blog not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_all_qna(request):
    from .models import Question
    questions = Question.objects.all().order_by('-date_added')
    data = [
        {
            'id': q.id,
            'username': q.user.username,
            'date_added': q.date_added,
            'title': q.title,
            'body': q.body,
            'category': q.category,
            'status': q.status,
        }
        for q in questions
    ]
    return JsonResponse({'questions': data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def get_my_qna(request):
    from .models import Question
    questions = Question.objects.filter(user=request.user).order_by('-date_added')
    data = [
        {
            'id': q.id,
            'username': q.user.username,
            'date_added': q.date_added,
            'title': q.title,
            'body': q.body,
            'category': q.category,
            'status': q.status,
        }
        for q in questions
    ]
    return JsonResponse({'questions': data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def get_qna_by_category(request, category):
    from .models import Question
    questions = Question.objects.filter(category=category).order_by('-date_added')
    data = [
        {
            'id': q.id,
            'username': q.user.username,
            'date_added': q.date_added,
            'title': q.title,
            'body': q.body,
            'category': q.category,
            'status': q.status,
        }
        for q in questions
    ]
    return JsonResponse({'questions': data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def create_question(request):
    from .models import Question
    data = json.loads(request.body)
    title = data.get('title')
    body = data.get('body')
    category = data.get('category')
    if not title or not body or not category:
        return JsonResponse({'error': 'Title, body, and category are required.'}, status=400)
    question = Question.objects.create(user=request.user, title=title, body=body, category=category)
    return JsonResponse({'message': 'Question created successfully.', 'question_id': question.id})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def close_question(request, question_id):
    from .models import Question
    try:
        question = Question.objects.get(id=question_id)
        if question.user != request.user:
            return JsonResponse({'error': 'You are not the creator of this question.'}, status=403)
        if question.status == 'closed':
            return JsonResponse({'message': 'Question is already closed.'})
        question.status = 'closed'
        question.save()
        return JsonResponse({'message': 'Question closed successfully.'})
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found.'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def create_comment(request, question_id):
    from .models import Question, Comment
    try:
        question = Question.objects.get(id=question_id)
        if question.status == 'closed':
            return JsonResponse({'error': 'Cannot comment on a closed question.'}, status=403)
        data = json.loads(request.body)
        body = data.get('body')
        if not body:
            return JsonResponse({'error': 'Body is required.'}, status=400)
        comment = Comment.objects.create(question=question, user=request.user, body=body)
        return JsonResponse({'message': 'Comment created successfully.', 'comment_id': comment.id})
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found.'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def thumbs_up_comment(request, comment_id):
    from .models import Comment, CommentThumbsUp
    try:
        comment = Comment.objects.get(id=comment_id)
        existing_thumbs_up = CommentThumbsUp.objects.filter(comment=comment, user=request.user).first()
        if existing_thumbs_up:
            existing_thumbs_up.delete()
            action = 'unliked'
        else:
            CommentThumbsUp.objects.create(comment=comment, user=request.user)
            action = 'liked'
        thumbs_up_count = comment.thumbs_ups.count()
        return JsonResponse({
            'message': f'Comment {action} successfully.',
            'action': action,
            'thumbs_up_count': thumbs_up_count
        })
    except Comment.DoesNotExist:
        return JsonResponse({'error': 'Comment not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def get_comments_by_question(request, question_id):
    from .models import Question, Comment
    try:
        question = Question.objects.get(id=question_id)
        comments = question.comments.all().order_by('date_added')
        data = [
            {
                'id': c.id,
                'username': c.user.username,
                'date_added': c.date_added,
                'body': c.body,
                'thumbs_up_count': c.thumbs_ups.count(),
            }
            for c in comments
        ]
        return JsonResponse({'comments': data})
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found.'}, status=404)
