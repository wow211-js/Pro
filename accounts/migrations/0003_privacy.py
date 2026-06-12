from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_chatmessage'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='visitorsession',
            name='ip_address',
        ),
        migrations.RemoveField(
            model_name='visitorsession',
            name='user_agent',
        ),
        migrations.AddField(
            model_name='visitorsession',
            name='ip_hash',
            field=models.CharField(blank=True, default='', max_length=16, verbose_name='Хэш IP'),
        ),
    ]
