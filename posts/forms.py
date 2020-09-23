from django.forms import ModelForm

from posts.models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            'group': 'Группа',
            'text': 'Текст новой записи',
            'image': 'Картинка к записи'
        }
        help_texts = {
            'group': (
                'Выберите группу для новой записи '
                'или оставьте поле пустым'
            ),
            'text': 'Введите текст новой записи и нажмите "Добавить"',
            'image': 'Загрузите картинку для записи или пропустите этот шаг'
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {
            'text': 'Текст комментария'
        }
        help_texts = {
            'text': 'Введите текст комментария и нажмите "Добавить"'
        }
