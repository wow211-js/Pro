from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_chatmessage_guest'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DirectMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(max_length=1000, verbose_name='Сообщение')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата отправки')),
                ('is_read', models.BooleanField(default=False, verbose_name='Прочитано')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to=settings.AUTH_USER_MODEL, verbose_name='Отправитель')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to=settings.AUTH_USER_MODEL, verbose_name='Получатель')),
            ],
            options={
                'verbose_name': 'личное сообщение',
                'verbose_name_plural': 'личные сообщения',
                'ordering': ['created_at'],
            },
        ),
    ]
