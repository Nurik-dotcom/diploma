from django.db import migrations
import random

def generate_account_number():
    return ''.join(random.choices('0123456789ABCDEF', k=16))

def populate_account_numbers(apps, schema_editor):
    User = apps.get_model('payments', 'User')
    for user in User.objects.all():
        if not user.account_number:
            unique_generated = False
            while not unique_generated:
                candidate = generate_account_number()
                if not User.objects.filter(account_number=candidate).exists():
                    user.account_number = candidate
                    unique_generated = True
            user.save()

class Migration(migrations.Migration):
    dependencies = [
        ('payments', '0004_user_account_number_user_account_status_and_more'),  # замените на точное имя файла
    ]

    operations = [
        migrations.RunPython(populate_account_numbers, reverse_code=migrations.RunPython.noop),
    ]
