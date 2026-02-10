from django.core.management.base import BaseCommand
from users.models import User
from django.contrib.auth.hashers import make_password
from decouple import config

class Command(BaseCommand):
    help = 'Reset admin password to match .env file'

    def handle(self, *args, **kwargs):
        admin_email = config('ADMIN_EMAIL', default='ramasnampoothiry@gmail.com')
        admin_password = config('ADMIN_PASSWORD', default='rama@admin123')
        
        try:
            admin = User.objects.get(email=admin_email)
            admin.password_hash = make_password(admin_password)
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'Admin password updated for {admin_email}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Admin user {admin_email} not found'))
