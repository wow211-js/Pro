from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ChatMessageForm, GuestChatMessageForm, SignUpForm
from .models import ChatMessage, VisitorSession


def _auto_clear_chat():
    """Delete messages older than 24 hours."""
    cutoff = timezone.now() - timedelta(hours=24)
    ChatMessage.objects.filter(created_at__lt=cutoff).delete()


def home(request):
    _auto_clear_chat()

    if request.method == 'POST':
        if request.user.is_authenticated:
            form = ChatMessageForm(request.POST)
            guest_form = GuestChatMessageForm()
            if form.is_valid():
                msg = form.save(commit=False)
                msg.user = request.user
                msg.save()
                return redirect('home')
        else:
            guest_form = GuestChatMessageForm(request.POST)
            form = ChatMessageForm()
            if guest_form.is_valid():
                msg = guest_form.save(commit=False)
                msg.user = None
                msg.save()
                return redirect('home')
    else:
        form = ChatMessageForm()
        guest_form = GuestChatMessageForm()

    chat_messages = list(ChatMessage.objects.select_related('user').order_by('-created_at')[:50])
    return render(request, 'accounts/home.html', {
        'chat_messages': reversed(chat_messages),
        'chat_form': form,
        'guest_form': guest_form,
    })


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
    return render(request, 'accounts/profile.html', {
        'chat_form': form,
        'chat_messages': reversed(chat_messages),
    })


@login_required
@user_passes_test(lambda user: user.is_staff)
def devices(request):
    visitors = VisitorSession.objects.select_related('user').filter(user__isnull=False)
    return render(request, 'accounts/devices.html', {
        'visitors': visitors,
        'online_after': timezone.now() - timedelta(minutes=5),
    })


@login_required
@user_passes_test(lambda user: user.is_staff)
@require_POST
def clear_chat(request):
    count, _ = ChatMessage.objects.all().delete()
    messages.success(request, f'Чат очищен. Удалено сообщений: {count}.')
    return redirect('home')
