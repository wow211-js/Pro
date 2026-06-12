from datetime import timedelta
import hashlib

from django.conf import settings
from django.db import models
from django.utils import timezone


def hash_ip(ip):
    """One-way hash of IP — allows deduplication without storing real IP."""
    if not ip:
        return None
    salt = getattr(settings, 'IP_HASH_SALT', 'default-salt')
    return hashlib.sha256(f"{salt}{ip}".encode()).hexdigest()[:16]




class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='profile',
    )
    display_name = models.CharField('Отображаемое имя', max_length=64, blank=True)

    class Meta:
        verbose_name = 'профиль'
        verbose_name_plural = 'профили'

    def __str__(self):
        return f'{self.user.username} ({self.display_name or "без имени"})' 

    @property
    def name(self):
        """Returns display_name if set, otherwise username."""
        return self.display_name or self.user.username

class VisitorSession(models.Model):
    session_key = models.CharField('Ключ сессии', max_length=64, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Пользователь',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    ip_hash = models.CharField('Хэш IP', max_length=16, blank=True, default='')
    first_seen = models.DateTimeField('Первый визит', auto_now_add=True)
    last_seen = models.DateTimeField('Последняя активность', auto_now=True)

    class Meta:
        ordering = ['-last_seen']
        verbose_name = 'устройство на сайте'
        verbose_name_plural = 'устройства на сайте'

    def __str__(self):
        owner = self.user.username if self.user else 'Гость'
        return f'{owner} - {self.ip_hash or "unknown"}'

    @property
    def is_online(self):
        return self.last_seen >= timezone.now() - timedelta(minutes=5)


class ChatMessage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Пользователь',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    guest_name = models.CharField('Имя гостя', max_length=32, blank=True, default='')
    text = models.TextField('Сообщение', max_length=1000)
    created_at = models.DateTimeField('Дата отправки', auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'сообщение чата'
        verbose_name_plural = 'сообщения чата'

    def __str__(self):
        name = self.user.username if self.user else self.guest_name or 'Гость'
        return f'{name}: {self.text[:40]}'

    @property
    def display_name(self):
        if self.user:
            try:
                dn = self.user.profile.display_name
                return dn if dn else self.user.username
            except Exception:
                return self.user.username
        return self.guest_name or 'Гость'


class DirectMessage(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Отправитель',
        related_name='sent_messages',
        on_delete=models.CASCADE,
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Получатель',
        related_name='received_messages',
        on_delete=models.CASCADE,
    )
    text = models.TextField('Сообщение', max_length=1000)
    created_at = models.DateTimeField('Дата отправки', auto_now_add=True)
    is_read = models.BooleanField('Прочитано', default=False)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'личное сообщение'
        verbose_name_plural = 'личные сообщения'

    def __str__(self):
        return f'{self.sender.username} → {self.recipient.username}: {self.text[:40]}'
