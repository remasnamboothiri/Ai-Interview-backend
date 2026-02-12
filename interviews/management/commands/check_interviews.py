from django.core.management.base import BaseCommand
from interviews.models import Interview

class Command(BaseCommand):
    help = 'Check for problematic interview records'

    def handle(self, *args, **options):
        self.stdout.write('Checking interviews...\n')
        
        interviews = Interview.objects.all()
        self.stdout.write(f'Total interviews: {interviews.count()}\n')
        
        for interview in interviews:
            issues = []
            
            if not interview.job:
                issues.append('Missing job')
            
            if not interview.candidate:
                issues.append('Missing candidate')
            elif not interview.candidate.user:
                issues.append('Candidate has no user')
            
            if issues:
                self.stdout.write(
                    self.style.WARNING(
                        f'Interview {interview.id}: {", ".join(issues)}'
                    )
                )
        
        self.stdout.write(self.style.SUCCESS('Check complete!'))
