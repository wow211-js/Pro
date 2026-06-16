from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ChatMessageForm, DirectMessageForm, ProfileEditForm, SignUpForm
from django.db import models
from .models import ChatMessage, DirectMessage, UserProfile


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
                dn = edit_form.cleaned_data['display_name'].strip()
                profile_obj.display_name = dn if dn else 'Гость'
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


@login_required
@require_POST
def delete_conversation(request, username):
    """Delete all direct messages between current user and partner."""
    from django.contrib.auth.models import User
    from django.db import models as dj_models

    try:
        partner = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, f'Пользователь "{username}" не найден.')
        return redirect('inbox')

    if partner == request.user:
        return redirect('inbox')

    count, _ = DirectMessage.objects.filter(
        dj_models.Q(sender=request.user, recipient=partner) |
        dj_models.Q(sender=partner, recipient=request.user)
    ).delete()

    messages.success(request, f'Диалог удалён. Удалено сообщений: {count}.')
    return redirect('inbox')


@login_required
def save_keys(request):
    """Save E2E keys for the user."""
    if request.method == 'POST':
        import json as _json
        try:
            data = _json.loads(request.body)
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.public_key = data.get('public_key', '')
            profile.encrypted_private_key = data.get('encrypted_private_key', '')
            profile.save()
            from django.http import JsonResponse
            return JsonResponse({'ok': True})
        except Exception as e:
            from django.http import JsonResponse
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    from django.http import HttpResponseNotAllowed
    return HttpResponseNotAllowed(['POST'])


@login_required
def get_public_key(request, username):
    """Get public key of a user. If requesting own keys, also return encrypted private key."""
    from django.contrib.auth.models import User
    from django.http import JsonResponse
    try:
        user = User.objects.get(username=username)
        profile = user.profile
        data = {'public_key': profile.public_key, 'username': username}
        # Only return private key to the owner (authenticated)
        if request.user.is_authenticated and request.user.username == username:
            data['encrypted_private_key'] = profile.encrypted_private_key
        return JsonResponse(data)
    except Exception:
        return JsonResponse({'error': 'not found'}, status=404)


@login_required
def poll_messages(request, username):
    """Return new messages since a given message ID."""
    from django.contrib.auth.models import User
    from django.http import JsonResponse
    from django.db import models as dj_models

    try:
        partner = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)

    since_id = int(request.GET.get('since', 0))

    msgs = DirectMessage.objects.filter(
        dj_models.Q(sender=request.user, recipient=partner) |
        dj_models.Q(sender=partner, recipient=request.user),
        id__gt=since_id,
    ).order_by('created_at').values('id', 'text', 'created_at', 'sender__username')

    # Mark incoming as read
    DirectMessage.objects.filter(
        sender=partner, recipient=request.user, is_read=False
    ).update(is_read=True)

    return JsonResponse({'messages': [
        {
            'id': m['id'],
            'text': m['text'],
            'created_at': m['created_at'].strftime('%d.%m %H:%M'),
            'is_mine': m['sender__username'] == request.user.username,
        }
        for m in msgs
    ]})


@login_required
def totp_setup(request):
    """Setup TOTP 2FA."""
    import pyotp, qrcode, io, base64 as b64
    from django.http import HttpResponse

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'generate':
            # Generate new secret
            secret = pyotp.random_base32()
            profile.totp_secret = secret
            profile.totp_enabled = False
            profile.save()
            return redirect('totp_setup')

        elif action == 'verify':
            code = request.POST.get('code', '').strip()
            if not profile.totp_secret:
                messages.error(request, 'Сначала сгенерируйте секрет.')
                return redirect('totp_setup')
            totp = pyotp.TOTP(profile.totp_secret)
            if totp.verify(code, valid_window=1):
                profile.totp_enabled = True
                profile.save()
                messages.success(request, '2FA успешно включена!')
                return redirect('profile')
            else:
                messages.error(request, 'Неверный код. Попробуйте ещё раз.')
                return redirect('totp_setup')

        elif action == 'disable':
            code = request.POST.get('code', '').strip()
            if profile.totp_enabled and profile.totp_secret:
                totp = pyotp.TOTP(profile.totp_secret)
                if totp.verify(code, valid_window=1):
                    profile.totp_enabled = False
                    profile.totp_secret = ''
                    profile.save()
                    messages.success(request, '2FA отключена.')
                    return redirect('profile')
                else:
                    messages.error(request, 'Неверный код.')
            return redirect('totp_setup')

    # Generate QR code if secret exists
    qr_data_url = None
    if profile.totp_secret:
        totp = pyotp.TOTP(profile.totp_secret)
        uri = totp.provisioning_uri(
            name=request.user.username,
            issuer_name='nizhnevartovsk86.ru'
        )
        img = qrcode.make(uri)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qr_data_url = 'data:image/png;base64,' + b64.b64encode(buf.getvalue()).decode()

    return render(request, 'accounts/totp_setup.html', {
        'profile': profile,
        'qr_data_url': qr_data_url,
    })


def totp_verify(request):
    """TOTP verification step after login."""
    if not request.session.get('totp_user_id'):
        return redirect('login')

    if request.method == 'POST':
        import pyotp
        from django.contrib.auth.models import User
        from django.contrib.auth import login as auth_login

        user_id = request.session.get('totp_user_id')
        try:
            user = User.objects.get(id=user_id)
            profile = user.profile
            code = request.POST.get('code', '').strip()
            totp = pyotp.TOTP(profile.totp_secret)
            if totp.verify(code, valid_window=1):
                del request.session['totp_user_id']
                auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return redirect('profile')
            else:
                messages.error(request, 'Неверный код.')
        except User.DoesNotExist:
            return redirect('login')

    return render(request, 'accounts/totp_verify.html')
