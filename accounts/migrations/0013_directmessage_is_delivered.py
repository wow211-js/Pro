from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_directmessage_edited_at_directmessage_is_deleted_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='directmessage',
            name='is_delivered',
            field=models.BooleanField(default=True, verbose_name='Доставлено'),
        ),
    ]
