from django.urls import path
from . import views

urlpatterns = [
    path('blogs/', views.get_all_blogs, name='get_all_blogs'),
    path('blogs/my/', views.get_my_blogs, name='get_my_blogs'),
    path('blogs/create/', views.create_blog, name='create_blog'),
    path('blogs/<int:blog_id>/edit/', views.edit_blog, name='edit_blog'),
    path('blogs/<int:blog_id>/delete/', views.delete_blog, name='delete_blog'),
    path('blogs/<int:blog_id>/thumbs-up/', views.thumbs_up_blog, name='thumbs_up_blog'),
    #mulai dari sini buat qna
    path('qna/', views.get_all_qna, name='get_all_qna'),
    path('qna/my/', views.get_my_qna, name='get_my_qna'),
    path('qna/category/<str:category>/', views.get_qna_by_category, name='get_qna_by_category'),
    path('qna/create/', views.create_question, name='create_question'),
    path('qna/<int:question_id>/comment/', views.create_comment, name='create_comment'),
    path('qna/comment/<int:comment_id>/thumbs-up/', views.thumbs_up_comment, name='thumbs_up_comment'),
    path('qna/<int:question_id>/close/', views.close_question, name='close_question'),
    path('qna/<int:question_id>/comments/', views.get_comments_by_question, name='get_comments_by_question'),
] 