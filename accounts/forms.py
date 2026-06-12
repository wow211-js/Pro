from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ChatMessage


class SignUpForm(UserCreationForm):
    display_name = forms.CharField(
        label='Отображаемое имя',
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Как вас видят другие'}),
        help_text='Необязательно. Если не указать — будет показан тег.',
    )

    class Meta:
        model = User
        fields = ('username', 'display_name', 'password1', 'password2')
        labels = {
            'username': 'Тег / логин (@)',
        }

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            from .models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.display_name = self.cleaned_data.get('display_name', '')
            profile.save()
        return user


class ProfileEditForm(forms.Form):
    display_name = forms.CharField(
        label='Отображаемое имя',
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Как вас видят другие'}),
    )


class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Написать сообщение...',
            })
        }
        labels = {'text': ''}


class GuestChatMessageForm(forms.ModelForm):
    guest_name = forms.CharField(
        max_length=32,
        required=True,
        label='',
        widget=forms.TextInput(attrs={'placeholder': 'Ваш ник'})
    )

    class Meta:
        model = ChatMessage
        fields = ('guest_name', 'text')
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Написать сообщение...',
            })
        }
        labels = {'text': ''}


class DirectMessageForm(forms.Form):
    text = forms.CharField(
        max_length=1000,
        label='',
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Написать сообщение...',
        })
    )
