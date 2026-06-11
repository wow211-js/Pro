from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import ChatMessageForm, SignUpForm
from .models import ChatMessage, VisitorSession


def home(request):
    return render(request, 'accounts/home.html')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Аккаунт создан. Добро пожаловать!')
            return redirect('profile')
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            chat_message = form.save(commit=False)
            chat_message.user = request.user
            chat_message.save()
            return redirect('profile')
    else:
        form = ChatMessageForm()

    chat_messages = list(ChatMessage.objects.select_related('user').order_by('-created_at')[:50])
    return render(
        request,
        'accounts/profile.html',
        {
            'chat_form': form,
            'chat_messages': reversed(chat_messages),
        },
    )


@login_required
@user_passes_test(lambda user: user.is_staff)
def devices(request):
    visitors = VisitorSession.objects.select_related('user').filter(user__isnull=False)
    return render(
        request,
        'accounts/devices.html',
        {
            'visitors': visitors,
            'online_after': timezone.now() - timedelta(minutes=5),
        },
    )
