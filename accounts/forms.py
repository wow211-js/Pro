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
            'text': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Напишите сообщение в общий чат',
                }
            )
        }
        labels = {
            'text': '',
        }
