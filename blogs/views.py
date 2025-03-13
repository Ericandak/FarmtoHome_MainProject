from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import BlogPost, Comment
from django.contrib import messages
from django.http import JsonResponse

@login_required
def blog_feed(request):
    # Get all posts for the feed
    posts = BlogPost.objects.select_related('author').prefetch_related('comments', 'likes').all()
    
    context = {
        'posts': posts,
        'username': request.user.username
    }
    return render(request, 'blogs/feed.html', context)

@login_required
def like_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(BlogPost, id=post_id)
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        return JsonResponse({'likes_count': post.likes.count(), 'liked': liked})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def create_post(request):

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        image = request.FILES.get('image')

        if title and content:
            post = BlogPost.objects.create(
                author=request.user,
                title=title,
                content=content,
                image=image
            )
            messages.success(request, 'Blog post created successfully!')
            return redirect('blogs:create_post')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return render(request, 'blogs/CreateBlog.html')

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    context = {
        'post': post,
        'username': request.user.username,
        'has_seller_role': request.user.role.filter(name='Seller').exists(),
    }
    return render(request, 'blogs/post_detail.html', context)

@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(BlogPost, id=post_id)
        content = request.POST.get('content')
        if content:
            Comment.objects.create(
                post=post,
                author=request.user,
                content=content
            )
            messages.success(request, 'Comment added successfully!')
        return redirect('blogs:post_detail', post_id=post_id)