from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_create_missing_profiles'),
    ]

    operations = [
        migrations.DeleteModel(name='VisitorSession'),
        migrations.AddField(
            model_name='userprofile',
            name='public_key',
            field=models.TextField(blank=True, verbose_name='Публичный ключ'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='encrypted_private_key',
            field=models.TextField(blank=True, verbose_name='Зашифрованный приватный ключ'),
        ),
    ]
