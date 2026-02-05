from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification
from users.models import User

class Command(BaseCommand):
    help = 'Create sample notifications for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to create notifications for',
            default=1
        )
        parser.add_argument(
            '--count',
            type=int,
            help='Number of notifications to create',
            default=10
        )

    def handle(self, *args, **options):
        user_id = options['user_id']
        count = options['count']

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with ID {user_id} does not exist')
            )
            return

        sample_notifications = [
            {
                'notification_type': 'interview_scheduled',
                'title': 'Interview Scheduled',
                'message': 'Your interview for Software Engineer position has been scheduled for tomorrow at 2:00 PM.',
            },
            {
                'notification_type': 'application_received',
                'title': 'New Application Received',
                'message': 'You have received a new application for the Frontend Developer position from John Doe.',
            },
            {
                'notification_type': 'result_available',
                'title': 'Interview Results Available',
                'message': 'The results for Sarah Smith\'s interview are now available for review.',
            },
            {
                'notification_type': 'application_status_changed',
                'title': 'Application Status Updated',
                'message': 'The application status for Backend Developer position has been changed to "Interviewing".',
            },
            {
                'notification_type': 'interview_reminder',
                'title': 'Interview Reminder',
                'message': 'Reminder: You have an interview scheduled in 1 hour with Mike Johnson.',
            },
            {
                'notification_type': 'interview_cancelled',
                'title': 'Interview Cancelled',
                'message': 'The interview scheduled for today at 3:00 PM has been cancelled by the candidate.',
            },
            {
                'notification_type': 'system_announcement',
                'title': 'System Maintenance',
                'message': 'The system will undergo maintenance tonight from 11:00 PM to 2:00 AM. Please save your work.',
            },
        ]

        created_count = 0
        for i in range(count):
            sample = sample_notifications[i % len(sample_notifications)]
            
            # Create notification with varying timestamps
            created_at = timezone.now() - timedelta(
                hours=i * 2,
                minutes=i * 15
            )
            
            notification = Notification.objects.create(
                user=user,
                notification_type=sample['notification_type'],
                title=f"{sample['title']} #{i + 1}",
                message=sample['message'],
                is_read=(i % 3 == 0),  # Make every 3rd notification read
                created_at=created_at
            )
            
            if notification.is_read:
                notification.read_at = created_at + timedelta(minutes=30)
                notification.save()
            
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} notifications for user {user.email}'
            )
        )