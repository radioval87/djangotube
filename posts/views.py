from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.select_related('author', 'group')
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page,
                                          'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author').all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group, 'page': page,
                                          'paginator': paginator})


@login_required
def new_post(request):
    if request.method != 'POST':
        form = PostForm()
        return render(request, 'new.html', {'form': form})
    post = Post(author=request.user)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('index')
    return render(request, 'new.html', {'form': form})


def profile(request, username):
    following = False
    profile_ = get_object_or_404(User, username=username)
    posts = profile_.posts.select_related('group').all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    if request.user.is_authenticated:
        following = request.user.follower.filter(author=profile_).exists()
    counters = count(profile_, posts)
    return render(request, 'profile.html', {'profile': profile_,
                                            'counters': counters, 'page': page,
                                            'paginator': paginator,
                                            'following': following})


def post_view(request, username, post_id):
    following = False
    profile_ = get_object_or_404(User, username=username)
    posts = profile_.posts.select_related('group').all()
    post = get_object_or_404(posts, id=post_id)
    comments = post.comments.select_related('author').all()
    form = CommentForm()
    if request.user.is_authenticated:
        following = request.user.follower.filter(author=profile_).exists()
    counters = count(profile_, posts)
    return render(request, 'post.html', {'profile': profile_,
                                         'counters': counters,
                                         'post': post, 'form': form,
                                         'comments': comments,
                                         'following': following})


def count(profile_, posts):
    nmbr_of_posts = posts.count()
    nmbr_of_subscriptions = profile_.follower.all().count()
    nmbr_of_followers = profile_.following.all().count()
    counters = {'posts': nmbr_of_posts,
                'subscriptions': nmbr_of_subscriptions,
                'followers': nmbr_of_followers}
    return counters


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if request.user != post.author:
        return redirect('post_view',
                        username=post.author.username, post_id=post_id)
    edit = True
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('post_view',
                            username=post.author.username, post_id=post_id)
    form = PostForm(instance=post)
    form['text'].help_text = (
        'Отредактируйте текст записи и '
        'нажмите "Сохранить"'
    )
    form['group'].help_text = 'Измените группу'
    form['text'].label = 'Текст записи'
    return render(request, 'new.html', {'form': form, 'edit': edit,
                                        'post': post})


@login_required
def add_comment(request, username, post_id):
    if request.method != 'POST':
        return redirect('post_view',
                        username=username, post_id=post_id)
    comment = Comment(author_id=request.user.id, post_id=post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
    return redirect('post_view',
                    username=username, post_id=post_id)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    print(posts.query)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page,
                                           'paginator': paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', username=username)
