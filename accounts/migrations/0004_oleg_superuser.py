from django.db import migrations


def make_oleg_superuser(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    try:
        user = User.objects.get(username='Oleg')
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print('Oleg promoted to superuser')
    except User.DoesNotExist:
        print('User Oleg not found')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_privacy'),
    ]

    operations = [
        migrations.RunPython(make_oleg_superuser, migrations.RunPython.noop),
    ]
