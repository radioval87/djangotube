import tempfile

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from .models import Follow, Group, Post, User

# import unittest


small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)


class TestMethods(TestCase):

    def setUp(self):
        self.unauth = Client()
        self.auth = Client()
        self.user = User.objects.create_user(
                    username='sarah', email='connor.s@skynet.com',
                    password='12345')
        self.auth.force_login(self.user)
        self.group = Group.objects.create(title='sarah',
                                          slug='sarah',
                                          description='Sarahs')
        self.text1 = 'there is no fate'
        self.john = User.objects.create_user(username='john',
                                             email='jconnor@skynet.com',
                                             password='12345')

    def test_page_is_created(self):
        response = self.auth.get(reverse('profile',
                                         kwargs={'username':
                                                 self.user.username}))
        self.assertEquals(response.status_code, 200)

    def test_auth_can_create_post(self):
        self.auth.post(reverse('new_post'), {'text': self.text1,
                                             'group': self.group.id})
        post = Post.objects.first()
        self.assertEquals(post.text, self.text1)
        self.assertEquals(post.group, self.group)
        response = self.auth.get(reverse('index'))
        self.assertContains(response, self.text1)
        self.assertContains(response, self.group.title)

    def test_unauth_is_redirected(self):
        reverse_login = reverse('login')
        reverse_new_post = reverse('new_post')
        response = self.unauth.post(reverse('new_post'))
        self.assertRedirects(response,
                             f'{reverse_login}?next={reverse_new_post}')

    def test_new_post(self):
        self.auth.post(reverse('new_post'), {'text': self.text1})
        cache.clear()
        self.compare(self.text1)

    def test_auth_can_update(self):
        response = self.auth.post(reverse('new_post'), {'text': self.text1})
        self.assertRedirects(response, reverse('index'))
        post = Post.objects.filter(author_id=self.user.id).get(text=self.text1)
        text2 = 'skynet my love'
        cache.clear()
        response = self.auth.post(reverse('post_edit',
                                          kwargs={'username':
                                                  self.user.username,
                                                  'post_id': post.id}),
                                  {'text': text2})
        self.assertRedirects(response, reverse('post_view',
                                               kwargs={'username':
                                                       self.user.username,
                                                       'post_id':
                                                       post.id}))
        self.compare(text2)

    def compare(self, text):
        post = Post.objects.filter(author_id=self.user.id).get(text=text)
        paths = [reverse('index'),
                 reverse('profile', kwargs={'username': self.user.username}),
                 reverse('post_view', kwargs={'username': self.user.username,
                                              'post_id': post.id})]
        for path in paths:
            response = self.auth.get(path)
            with self.subTest(path=path):
                self.assertContains(response, text)

    def test_404(self):
        response = self.unauth.get(reverse('profile', kwargs={'username':
                                                              'QWs0qs0DD'}))
        self.assertEquals(response.status_code, 404)

    def test_page_includes_img(self):
        image = SimpleUploadedFile('small.gif', small_gif,
                                   content_type='image/gif')
        self.auth.post(reverse('new_post'), {'text': self.text1,
                                             'group': self.group.id,
                                             'image': image})
        post = Post.objects.filter(author_id=self.user.id).get(
            text=self.text1
        )
        response = self.auth.get(reverse('post_view',
                                         kwargs={'username':
                                                 self.user.username,
                                                 'post_id': post.id}))
        self.assertContains(response, '<img class=')
        response = self.auth.get(reverse('index'))
        self.assertContains(response, '<img class=')
        response = self.auth.get(reverse('group_posts',
                                         kwargs={'slug': self.group.slug}))
        self.assertContains(response, '<img class=')

    def test_extension_protection(self):
        with tempfile.NamedTemporaryFile(suffix='.md') as image:
            response = self.auth.post(reverse('new_post'), {'text': self.text1,
                                                            'image': image})
        form = response.context['form']
        self.assertFormError(response, 'form', 'image', form.errors['image'])

    def test_cache(self):
        self.auth.post(reverse('new_post'), {'text': self.text1})
        response = self.auth.get(reverse('index'))
        self.assertNotContains(response, self.text1)
        cache.clear()
        response = self.auth.get(reverse('index'))
        self.assertContains(response, self.text1)

    def test_auth_can_sub(self):
        self.auth.post(reverse('profile_follow',
                               kwargs={'username': self.john.username}))
        self.assertIsInstance(self.user.follower.first(), Follow)

    def test_auth_can_unsub(self):
        Follow.objects.create(user=self.user, author=self.john)
        self.assertTrue(self.user.follower.all())
        self.auth.post(reverse('profile_unfollow',
                               kwargs={'username': self.john.username}))
        self.assertFalse(self.user.follower.all())

    def test_news_subscribed(self):
        self.auth.post(reverse('new_post'), {'text': self.text1})
        cache.clear()
        self.auth.logout()
        self.auth.force_login(self.john)
        self.auth.post(reverse('profile_follow',
                               kwargs={'username': 'sarah'}))
        response = self.auth.get(reverse('follow_index'))
        self.assertContains(response, self.text1)

    def test_news_not_subscribed(self):
        self.auth.post(reverse('new_post'), {'text': self.text1})
        cache.clear()
        self.auth.logout()
        arnie = User.objects.create_user(username='arnie',
                                         email='arnie@skynet.com',
                                         password='12345')
        self.auth.force_login(arnie)
        response = self.auth.get(reverse('follow_index'))
        self.assertNotContains(response, self.text1)

    def test_auth_can_comment(self):
        text2 = 'sure about this'
        post = Post.objects.create(text=self.text1, author=self.user)
        self.auth.post(reverse('add_comment', kwargs={'username':
                                                      self.user.username,
                                                      'post_id': post.id}),
                       {'text': text2})
        response = self.auth.get(reverse('post_view', kwargs={
                                            'username': self.user.username,
                                            'post_id': post.id}))
        self.assertContains(response, text2)

    def test_unauth_cant_comment(self):
        text2 = 'where is my comment?'
        post = Post.objects.create(text=self.text1, author=self.user)
        self.unauth.post(reverse('add_comment', kwargs={'username':
                                                        self.user.username,
                                                        'post_id': post.id}),
                         {'text': text2})
        response = self.unauth.get(reverse('post_view', kwargs={
                                           'username': self.user.username,
                                           'post_id': post.id}))
        self.assertNotContains(response, text2)
