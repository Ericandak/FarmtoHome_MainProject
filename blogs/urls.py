from django.urls import path
from . import views

app_name = 'blogs'

urlpatterns = [
    path('feed/', views.blog_feed, name='feed'),
    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
]