from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_e2e_remove_visitor'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='totp_secret',
            field=models.CharField(blank=True, max_length=32, verbose_name='TOTP секрет'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='totp_enabled',
            field=models.BooleanField(default=False, verbose_name='2FA включена'),
        ),
    ]
