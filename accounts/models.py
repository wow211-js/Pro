import hashlib
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class UserBlock(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='blocks_made',
        on_delete=models.CASCADE,
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='blocks_received',
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')
        verbose_name = 'блокировка'
        verbose_name_plural = 'блокировки'

    def __str__(self):
        return f'{self.blocker.username} → {self.blocked.username}'


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='profile',
    )
    display_name = models.CharField('Отображаемое имя', max_length=64, blank=True)
    totp_secret = models.CharField('TOTP секрет', max_length=32, blank=True)
    totp_enabled = models.BooleanField('2FA включена', default=False)
    public_key = models.TextField('Публичный ключ', blank=True)
    encrypted_private_key = models.TextField('Зашифрованный приватный ключ', blank=True)

    class Meta:
        verbose_name = 'профиль'
        verbose_name_plural = 'профили'

    def __str__(self):
        return f'{self.user.username} ({self.display_name or "без имени"})'

    @property
    def name(self):
        return self.display_name or self.user.username


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
        return self.guest_name if self.guest_name and self.guest_name.strip() else 'Гость'


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
    # Encrypted ciphertext (base64 encoded)
    text = models.TextField('Сообщение (зашифровано)')
    created_at = models.DateTimeField('Дата отправки', auto_now_add=True)
    is_read = models.BooleanField('Прочитано', default=False)
    is_deleted = models.BooleanField('Удалено', default=False)
    is_edited = models.BooleanField('Изменено', default=False)
    # Reply to another message (threading)
    reply_to = models.ForeignKey(
        'self',
        verbose_name='Ответ на',
        related_name='replies',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    # Soft delete + edit tracking
    is_deleted = models.BooleanField('Удалено', default=False)
    is_edited = models.BooleanField('Изменено', default=False)
    edited_at = models.DateTimeField('Дата изменения', null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'личное сообщение'
        verbose_name_plural = 'личные сообщения'

    def __str__(self):
        return f'{self.sender.username} → {self.recipient.username}: [encrypted]'
