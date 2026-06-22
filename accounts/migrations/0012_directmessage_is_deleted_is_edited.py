from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_alter_directmessage_text_userblock'),
    ]

    operations = [
        migrations.AddField(
            model_name='directmessage',
            name='is_deleted',
            field=models.BooleanField(default=False, verbose_name='Удалено'),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='is_edited',
            field=models.BooleanField(default=False, verbose_name='Изменено'),
        ),
    ]
