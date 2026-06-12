from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ChatMessage


class SignUpForm(UserCreationForm):
    email = forms.EmailField(label='Email', required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        labels = {
            'username': 'Имя пользователя',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


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
