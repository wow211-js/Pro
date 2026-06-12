from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ChatMessageForm, DirectMessageForm, ProfileEditForm, SignUpForm
from django.db import models
from .models import ChatMessage, DirectMessage, UserProfile, VisitorSession


def _auto_clear_chat():
    cutoff = timezone.now() - timedelta(hours=24)
    ChatMessage.objects.filter(created_at__lt=cutoff).delete()


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
    _auto_clear_chat()
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)

    chat_form = ChatMessageForm()
    edit_form = ProfileEditForm(initial={'display_name': profile_obj.display_name})

    if request.method == 'POST':
        if 'text' in request.POST:
            chat_form = ChatMessageForm(request.POST)
            if chat_form.is_valid():
                msg = chat_form.save(commit=False)
                msg.user = request.user
                msg.save()
                return redirect('profile')
        elif 'display_name' in request.POST:
            edit_form = ProfileEditForm(request.POST)
            if edit_form.is_valid():
                profile_obj.display_name = edit_form.cleaned_data['display_name']
                profile_obj.save()
                messages.success(request, 'Имя обновлено.')
                return redirect('profile')

    chat_messages = list(ChatMessage.objects.select_related('user').order_by('-created_at')[:50])
    return render(request, 'accounts/profile.html', {
        'chat_form': chat_form,
        'edit_form': edit_form,
        'chat_messages': reversed(chat_messages),
        'profile': profile_obj,
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
    return redirect('profile')


@login_required
def inbox(request):
    """List of all conversations for current user."""
    from django.db.models import Q, Max, OuterRef, Subquery
    from django.contrib.auth.models import User

    # Get all users this person has exchanged messages with
    sent_to = DirectMessage.objects.filter(sender=request.user).values_list('recipient', flat=True)
    received_from = DirectMessage.objects.filter(recipient=request.user).values_list('sender', flat=True)
    partner_ids = set(list(sent_to) + list(received_from))
    partners = User.objects.filter(id__in=partner_ids)

    conversations = []
    for partner in partners:
        last_msg = DirectMessage.objects.filter(
            (models.Q(sender=request.user, recipient=partner) |
             models.Q(sender=partner, recipient=request.user))
        ).last()
        unread = DirectMessage.objects.filter(sender=partner, recipient=request.user, is_read=False).count()
        conversations.append({
            'partner': partner,
            'last_msg': last_msg,
            'unread': unread,
        })

    conversations.sort(key=lambda x: x['last_msg'].created_at if x['last_msg'] else timezone.now(), reverse=True)

    return render(request, 'accounts/inbox.html', {'conversations': conversations})


@login_required
def conversation(request, username):
    from django.contrib.auth.models import User
    from django.db import models as dj_models

    try:
        partner = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, f'Пользователь "{username}" не найден.')
        return redirect('inbox')

    if partner == request.user:
        return redirect('inbox')

    # Mark incoming as read
    DirectMessage.objects.filter(sender=partner, recipient=request.user, is_read=False).update(is_read=True)

    if request.method == 'POST':
        form = DirectMessageForm(request.POST)
        if form.is_valid():
            DirectMessage.objects.create(
                sender=request.user,
                recipient=partner,
                text=form.cleaned_data['text'],
            )
            return redirect('conversation', username=username)
    else:
        form = DirectMessageForm()

    msgs = DirectMessage.objects.filter(
        dj_models.Q(sender=request.user, recipient=partner) |
        dj_models.Q(sender=partner, recipient=request.user)
    ).order_by('created_at')

    return render(request, 'accounts/conversation.html', {
        'partner': partner,
        'msgs': msgs,
        'form': form,
    })


@login_required
def new_conversation(request):
    """Search users by tag and start a conversation."""
    from django.contrib.auth.models import User
    from django.db.models import Q

    query = request.GET.get('q', '').strip().lstrip('@')
    results = []

    if request.method == 'POST':
        username = request.POST.get('username', '').strip().lstrip('@')
        if not username:
            messages.error(request, 'Введите тег пользователя.')
        else:
            try:
                User.objects.get(username=username)
                return redirect('conversation', username=username)
            except User.DoesNotExist:
                messages.error(request, f'Пользователь @{username} не найден.')

    if query:
        results = User.objects.filter(
            Q(username__icontains=query)
        ).exclude(id=request.user.id).select_related('profile')[:10]

    return render(request, 'accounts/new_conversation.html', {
        'query': query,
        'results': results,
    })
