from django.core.management.base import BaseCommand
from users.models import User
from django.contrib.auth.hashers import make_password
from decouple import config

class Command(BaseCommand):
    help = 'Create initial admin user from environment variables'

    def handle(self, *args, **kwargs):
        # Get credentials from environment variables
        admin_email = config('ADMIN_EMAIL', default=None)
        admin_password = config('ADMIN_PASSWORD', default=None)
        admin_name = config('ADMIN_NAME', default='Super Admin')
        
        # Only create if environment variables are set
        if not admin_email or not admin_password:
            self.stdout.write(self.style.WARNING(
                'ADMIN_EMAIL and ADMIN_PASSWORD not set in environment variables. Skipping admin creation.'
            ))
            return
        
        # Check if admin already exists
        if User.objects.filter(email=admin_email).exists():
            # UPDATE the existing admin password
            admin = User.objects.get(email=admin_email)
            admin.password_hash = make_password(admin_password)
            admin.full_name = admin_name
            admin.is_active = True
            admin.is_email_verified = True
            admin.save()
            self.stdout.write(self.style.SUCCESS(
                f'Admin user {admin_email} password updated successfully.'
            ))
            return
        
        # Create admin user
        User.objects.create(
            email=admin_email,
            password_hash=make_password(admin_password),
            full_name=admin_name,
            user_type='admin',
            is_active=True,
            is_email_verified=True
        )
        
        self.stdout.write(self.style.SUCCESS(
            f'Admin user created: {admin_email}'
        ))
