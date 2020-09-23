from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import Truncator

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=60, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField('date published', auto_now_add=True,
                                    db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='posts')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True,
                              null=True, related_name='posts')
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        text_beginning = Truncator(self.text).words(10, truncate='...')
        return text_beginning


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True,
                             null=True, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField()
    created = models.DateTimeField('date created', auto_now_add=True)


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='following')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'author'],
                                               name='unique_follow'), ]
