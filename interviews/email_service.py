"""
Email Service for Interview Invitations
Sends email to candidates when interview is scheduled
"""

from django.core.mail import send_mail
from django.conf import settings
from decouple import config
from datetime import datetime
from interviews.models import Interview


class InterviewEmailService:
    """
    Service to send interview invitation emails
    """
    
    @staticmethod
    def send_interview_invitation(interview_id: int) -> bool:
        """
        Send interview invitation email to candidate
        
        Args:
            interview_id: ID of the interview
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Get interview details
            interview = Interview.objects.select_related(
                'job', 'candidate', 'candidate__user', 'agent', 'recruiter'
            ).get(id=interview_id)
            
            # Get candidate email
            candidate_email = interview.candidate.user.email
            candidate_name = interview.candidate.user.full_name
            
            # Build interview link using UUID
            frontend_url = config('FRONTEND_URL', default='http://localhost:5173')
            #interview_link = f"{frontend_url}/candidate/interview/{interview.uuid}"
            interview_link = f"{frontend_url}/interview/invitation/{interview.id}"


            
            
            # Format scheduled time
            scheduled_time = interview.scheduled_at.strftime("%B %d, %Y at %I:%M %p")
            
            # Email subject
            subject = f"Interview Invitation - {interview.job.title}"
            
            
            # Email body
            message = f"""
            Dear {candidate_name},

You have been invited to attend an interview for the position of {interview.job.title} at {interview.job.company.name}.

INTERVIEW DETAILS:
Date & Time: {scheduled_time}
Duration: {interview.duration_minutes} minutes
Position: {interview.job.title}
Company: {interview.job.company.name}
Interview Type: {interview.get_interview_type_display()}

INTERVIEW LINK:
{interview_link}

PREPARATION CHECKLIST:
1. Click the link above at the scheduled time
2. Ensure you have a stable internet connection
3. Allow camera and microphone access when prompted
4. Find a quiet, well-lit space for the interview
5. Have your resume and relevant documents ready

{interview.instructions if interview.instructions else ''}

TECHNICAL REQUIREMENTS:
- Working webcam and microphone
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Stable internet connection (minimum 5 Mbps)

If you have any questions or need to reschedule, please reply to this email.

Best of luck with your interview!

Best regards,
{interview.recruiter.full_name if interview.recruiter else 'The Recruitment Team'}
{interview.job.company.name}
"""

            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@aiinterview.com',
                recipient_list=[candidate_email],
                fail_silently=False,
            )
            
            # Update interview record
            interview.email_sent = True
            interview.email_sent_at = datetime.now()
            interview.candidate_notified = True
            interview.save()
            
            return True
            
        except Interview.DoesNotExist:
            print(f"Interview with ID {interview_id} not found")
            return False
        except Exception as e:
            print(f"Error sending interview invitation email: {str(e)}")
            return False
    
    @staticmethod
    def send_interview_reminder(interview_id: int) -> bool:
        """
        Send reminder email 24 hours before interview
        
        Args:
            interview_id: ID of the interview
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            interview = Interview.objects.select_related(
                'job', 'candidate', 'candidate__user'
            ).get(id=interview_id)
            
            candidate_email = interview.candidate.user.email
            candidate_name = interview.candidate.user.full_name
            
            frontend_url = config('FRONTEND_URL', default='http://localhost:5173')
            #interview_link = f"{frontend_url}/candidate/interview/{interview.uuid}"
            interview_link = f"{frontend_url}/interview/invitation/{interview.id}"

            
            scheduled_time = interview.scheduled_at.strftime("%B %d, %Y at %I:%M %p")
            
            subject = f"Reminder: Interview Tomorrow - {interview.job.title}"
            
            message = f"""
Dear {candidate_name},

This is a friendly reminder about your upcoming interview scheduled for tomorrow.

Interview Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date & Time: {scheduled_time}
💼 Position: {interview.job.title}

Interview Link:
{interview_link}

Please ensure you're ready 5-10 minutes before the scheduled time.

Good luck!

Best regards,
The Recruitment Team
"""
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@aiinterview.com',
                recipient_list=[candidate_email],
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending reminder email: {str(e)}")
            return False
    
    @staticmethod
    def send_interview_cancellation(interview_id: int, reason: str = "") -> bool:
        """
        Send cancellation email to candidate
        
        Args:
            interview_id: ID of the interview
            reason: Reason for cancellation
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            interview = Interview.objects.select_related(
                'job', 'candidate', 'candidate__user'
            ).get(id=interview_id)
            
            candidate_email = interview.candidate.user.email
            candidate_name = interview.candidate.user.full_name
            
            subject = f"Interview Cancelled - {interview.job.title}"
            
            message = f"""
Dear {candidate_name},

We regret to inform you that your interview for the position of {interview.job.title} has been cancelled.

{f"Reason: {reason}" if reason else ""}

We apologize for any inconvenience this may cause. We will reach out to you if we wish to reschedule.

Best regards,
The Recruitment Team
"""
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@aiinterview.com',
                recipient_list=[candidate_email],
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending cancellation email: {str(e)}")
            return False
