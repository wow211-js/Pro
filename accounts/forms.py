import json
import re
import urllib.error
import urllib.parse
import urllib.request

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import ChatMessage


# XSS dangerous patterns (from API schema validation skill)
XSS_DANGEROUS_PATTERNS = [
    r'<script', r'javascript:', r'onerror=', r'onload=', r'onmouseover=',
    r'onclick=', r'onfocus=', r'onblur=', r'ondblclick=', r'onchange=',
    r'onsubmit=', r'onmouseenter=', r'onmouseleave=', r'onkeydown=',
    r'onkeypress=', r'onkeyup=', r'oncontextmenu=', r'data:text/html',
    r'data:application/javascript', r'eval\s*\(', r'expression\s*\(',
]
XSS_RE = re.compile('|'.join(XSS_DANGEROUS_PATTERNS), re.IGNORECASE)

def validate_no_xss(text):
    if XSS_RE.search(text):
        raise ValidationError('Ввод содержит недопустимые символы (XSS-паттерн).')


class SignUpForm(UserCreationForm):
    display_name = forms.CharField(
        label='Отображаемое имя',
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Как вас видят другие'}),
        help_text='Необязательно. Если не указать — будет показан тег.',
    )
    turnstile_token = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )

    class Meta:
        model = User
        fields = ('username', 'display_name', 'password1', 'password2', 'turnstile_token')
        labels = {
            'username': 'Тег / логин (@)',
        }

    def clean_turnstile_token(self):
        token = self.cleaned_data.get('turnstile_token', '')
        secret = getattr(settings, 'TURNSTILE_SECRET_KEY', '')
        # Skip validation if Turnstile not configured (dev mode)
        if not secret:
            return token
        if not token:
            raise ValidationError('Пожалуйста, пройдите проверку капчи.')
        try:
            data = urllib.parse.urlencode({'secret': secret, 'response': token}).encode()
            req = urllib.request.Request(
                'https://challenges.cloudflare.com/turnstile/v0/siteverify',
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read().decode())
            if not result.get('success'):
                raise ValidationError('Проверка капчи не пройдена. Попробуйте ещё раз.')
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
            raise ValidationError('Ошибка проверки капчи. Попробуйте позже.')
        return token

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            from .models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            dn = self.cleaned_data.get('display_name', '').strip()
            profile.display_name = dn if dn else 'Гость'
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

    def clean_text(self):
        text = self.cleaned_data.get('text', '')
        validate_no_xss(text)
        return text


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

    def clean_text(self):
        text = self.cleaned_data.get('text', '')
        validate_no_xss(text)
        return text

    def clean_guest_name(self):
        name = self.cleaned_data.get('guest_name', '')
        validate_no_xss(name)
        return name


class DirectMessageForm(forms.Form):
    text = forms.CharField(
        max_length=10000,
        label='',
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Написать сообщение...',
        })
    )

    def clean_text(self):
        text = self.cleaned_data.get('text', '')
        validate_no_xss(text)
        return text
