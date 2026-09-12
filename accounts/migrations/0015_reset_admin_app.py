from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_admin(apps, schema_editor):
    User = apps.get_model('auth', 'User')  
    User.objects.update_or_create(
        username='Oleg',
        defaults={
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
            'password': make_password('4r5tt5r4'),
        }
    )

def reverse_noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0014_callsignal'),  
    ]
    operations = [
        migrations.RunPython(create_admin, reverse_noop),
    ]
