"""
Email Service for Interview Invitations
Sends email to candidates when interview is scheduled
"""

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from decouple import config
from datetime import datetime
from interviews.models import Interview
import textwrap


class InterviewEmailService:
    """
    Service to send interview invitation emails
    """

    @staticmethod
    def _get_from_email():
        """Get properly configured from email"""
        return getattr(settings, 'DEFAULT_FROM_EMAIL', config('DEFAULT_FROM_EMAIL', default='noreply@aiinterview.com'))

    @staticmethod
    def _send_html_email(subject: str, plain_text: str, html_content: str, recipient: str) -> None:
        """
        Send email with both plain text and HTML versions.
        Having both reduces spam score significantly.
        """
        from_email = InterviewEmailService._get_from_email()
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_text,
            from_email=from_email,
            to=[recipient],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

    @staticmethod
    def send_interview_invitation(interview_id: int) -> bool:
        """
        Send interview invitation email to candidate
        """
        try:
            interview = Interview.objects.select_related(
                'job', 'candidate', 'candidate__user', 'agent', 'recruiter'
            ).get(id=interview_id)

            candidate_email = interview.candidate.user.email
            candidate_name = interview.candidate.user.full_name
            company_name = interview.job.company.name
            job_title = interview.job.title
            recruiter_name = interview.recruiter.full_name if interview.recruiter else 'The Recruitment Team'
            recruiter_email = interview.recruiter.email if interview.recruiter else ''

            frontend_url = config('FRONTEND_URL', default='http://localhost:5173')
            # Use UUID-based link (secure, unguessable)
            interview_link = interview.meeting_link or f"{frontend_url}/interview/system-check/{interview.uuid}"

            scheduled_time = interview.scheduled_at.strftime("%B %d, %Y at %I:%M %p")
            interview_type = interview.get_interview_type_display()
            duration = interview.duration_minutes
            instructions = interview.instructions or ''

            # ── Plain text version ──
            instructions_text = f"\nSPECIAL INSTRUCTIONS:\n{instructions}" if instructions else ''

            plain_text = textwrap.dedent(f"""\
                Dear {candidate_name},

                You have been invited to attend an AI-powered interview for the position of {job_title} at {company_name}.

                INTERVIEW DETAILS:
                Date & Time: {scheduled_time}
                Duration: {duration} minutes
                Position: {job_title}
                Company: {company_name}
                Interview Type: {interview_type}

                YOUR INTERVIEW LINK:
                {interview_link}

                IMPORTANT - PLEASE READ CAREFULLY BEFORE JOINING:

                1. THIS IS A ONE-TIME INTERVIEW LINK
                   Once you start the interview, you must complete it in one session.
                   The interview link cannot be used again after the session begins.
                   Do not close the browser tab or leave the page during the interview.

                2. INTERNET CONNECTION IS CRITICAL
                   You must be in a location with a strong and stable internet connection.
                   A weak or unstable connection will disrupt your interview session.
                   We strongly recommend using a wired connection or strong WiFi signal.
                   Minimum required speed: 5 Mbps (test your speed at fast.com before joining).

                3. IF YOUR INTERVIEW IS INTERRUPTED
                   If your session is cut short due to technical issues, power failure,
                   or any other reason, the interview link WILL NOT work again.
                   In this case, please immediately send an email to your recruiter at:
                   {recruiter_email}
                   Explain the issue and request a new interview to be scheduled.
                   Do not attempt to use the same link again as it will not work.

                PREPARATION CHECKLIST:
                1. Test your internet speed before the interview (minimum 5 Mbps)
                2. Use a laptop or desktop computer (not a mobile phone)
                3. Use Google Chrome or Microsoft Edge browser for best results
                4. Allow camera and microphone access when the browser asks
                5. Find a quiet, well-lit, distraction-free room
                6. Keep your resume and relevant documents ready
                7. Join 5 minutes before the scheduled time to test your setup
                8. Close all other browser tabs and applications to save bandwidth

                TECHNICAL REQUIREMENTS:
                - Working webcam and microphone (headset recommended for better audio)
                - Google Chrome or Microsoft Edge browser (latest version)
                - Stable internet connection (minimum 5 Mbps)
                - Laptop or desktop computer
                {instructions_text}

                If you have any questions before the interview, please contact your recruiter:
                Name: {recruiter_name}
                Email: {recruiter_email}

                We wish you the very best for your interview!

                Best regards,
                {recruiter_name}
                {company_name}
            """)

            # ── HTML version ──
            instructions_html = f"""
              <tr>
                <td style="padding:12px 24px;">
                  <div style="background-color:#fef3c7;border:1px solid #fde68a;border-radius:8px;padding:16px;">
                    <p style="color:#92400e;font-size:13px;font-weight:600;margin:0 0 8px;">SPECIAL INSTRUCTIONS</p>
                    <p style="color:#78350f;font-size:14px;margin:0;line-height:1.5;">{instructions}</p>
                  </div>
                </td>
              </tr>
            """ if instructions else ''

            recruiter_contact_html = f"""
              <p style="color:#555;font-size:13px;margin:8px 0 0;">
                Contact recruiter: <strong>{recruiter_name}</strong>
                {f' &mdash; <a href="mailto:{recruiter_email}" style="color:#7c3aed;">{recruiter_email}</a>' if recruiter_email else ''}
              </p>
            """ if recruiter_email else ''

            html_content = f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f4f4f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f7;padding:20px 0;">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

  <!-- Header -->
  <tr>
    <td style="background:linear-gradient(135deg,#7c3aed,#3b82f6);padding:32px 20px;text-align:center;">
      <h1 style="color:#ffffff;margin:0;font-size:22px;font-weight:600;">Interview Invitation</h1>
      <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;font-size:14px;">{job_title} at {company_name}</p>
    </td>
  </tr>

  <!-- Greeting -->
  <tr>
    <td style="padding:28px 24px 12px;">
      <p style="color:#333;font-size:15px;line-height:1.6;margin:0 0 16px;">Dear {candidate_name},</p>
      <p style="color:#555;font-size:14px;line-height:1.6;margin:0 0 20px;">
        You have been invited to attend an AI-powered interview for the position of <strong>{job_title}</strong> at <strong>{company_name}</strong>.
      </p>
    </td>
  </tr>

  <!-- Interview Details Card -->
  <tr>
    <td style="padding:0 24px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8f7ff;border-radius:8px;border:1px solid #e8e5f0;">
        <tr><td style="padding:20px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="padding:6px 0;color:#7c3aed;font-size:13px;font-weight:600;width:140px;">Date &amp; Time</td>
              <td style="padding:6px 0;color:#333;font-size:14px;">{scheduled_time}</td>
            </tr>
            <tr>
              <td style="padding:6px 0;color:#7c3aed;font-size:13px;font-weight:600;">Duration</td>
              <td style="padding:6px 0;color:#333;font-size:14px;">{duration} minutes</td>
            </tr>
            <tr>
              <td style="padding:6px 0;color:#7c3aed;font-size:13px;font-weight:600;">Position</td>
              <td style="padding:6px 0;color:#333;font-size:14px;">{job_title}</td>
            </tr>
            <tr>
              <td style="padding:6px 0;color:#7c3aed;font-size:13px;font-weight:600;">Company</td>
              <td style="padding:6px 0;color:#333;font-size:14px;">{company_name}</td>
            </tr>
            <tr>
              <td style="padding:6px 0;color:#7c3aed;font-size:13px;font-weight:600;">Interview Type</td>
              <td style="padding:6px 0;color:#333;font-size:14px;">{interview_type}</td>
            </tr>
          </table>
        </td></tr>
      </table>
    </td>
  </tr>

  <!-- CTA Button -->
  <tr>
    <td style="padding:24px;text-align:center;">
      <a href="{interview_link}" target="_blank"
         style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#7c3aed,#3b82f6);color:#ffffff;text-decoration:none;border-radius:8px;font-size:15px;font-weight:600;letter-spacing:0.3px;">
        Join Interview
      </a>
      <p style="color:#999;font-size:12px;margin:12px 0 0;">Or copy this link: <a href="{interview_link}" style="color:#7c3aed;word-break:break-all;">{interview_link}</a></p>
    </td>
  </tr>

  <!-- Important Warning -->
  <tr>
    <td style="padding:0 24px;">
      <div style="background-color:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:16px;">
        <p style="color:#dc2626;font-size:14px;font-weight:700;margin:0 0 12px;">&#9888; IMPORTANT - PLEASE READ CAREFULLY</p>

        <p style="color:#991b1b;font-size:13px;font-weight:600;margin:0 0 4px;">1. ONE-TIME INTERVIEW LINK</p>
        <p style="color:#7f1d1d;font-size:13px;margin:0 0 12px;line-height:1.5;">Once you start, you must complete the interview in one session. The link cannot be reused after the session begins. Do not close the browser tab or leave the page.</p>

        <p style="color:#991b1b;font-size:13px;font-weight:600;margin:0 0 4px;">2. INTERNET CONNECTION IS CRITICAL</p>
        <p style="color:#7f1d1d;font-size:13px;margin:0 0 12px;line-height:1.5;">Use a strong, stable internet connection (minimum 5 Mbps). Test your speed at <a href="https://fast.com" style="color:#7c3aed;">fast.com</a> before joining. A wired connection or strong WiFi is recommended.</p>

        <p style="color:#991b1b;font-size:13px;font-weight:600;margin:0 0 4px;">3. IF YOUR INTERVIEW IS INTERRUPTED</p>
        <p style="color:#7f1d1d;font-size:13px;margin:0;line-height:1.5;">If your session is cut short for any reason, the link will not work again. Email your recruiter immediately at <a href="mailto:{recruiter_email}" style="color:#7c3aed;">{recruiter_email}</a> to request a new interview.</p>
      </div>
    </td>
  </tr>

  {instructions_html}

  <!-- Preparation Checklist -->
  <tr>
    <td style="padding:20px 24px;">
      <h3 style="color:#333;font-size:14px;margin:0 0 12px;font-weight:600;">Preparation Checklist</h3>
      <table role="presentation" cellpadding="0" cellspacing="0">
        <tr><td style="padding:4px 8px 4px 0;color:#22c55e;font-size:14px;">&#10003;</td><td style="padding:4px 0;color:#555;font-size:13px;">Test internet speed (minimum 5 Mbps)</td></tr>
        <tr><td style="padding:4px 8px 4px 0;color:#22c55e;font-size:14px;">&#10003;</td><td style="padding:4px 0;color:#555;font-size:13px;">Use a laptop or desktop (not mobile)</td></tr>
        <tr><td style="padding:4px 8px 4px 0;color:#22c55e;font-size:14px;">&#10003;</td><td style="padding:4px 0;color:#555;font-size:13px;">Use Chrome or Edge browser (latest version)</td></tr>
        <tr><td style="padding:4px 8px 4px 0;color:#22c55e;font-size:14px;">&#10003;</td><td style="padding:4px 0;color:#555;font-size:13px;">Allow camera and microphone access</td></tr>
        <tr><td style="padding:4px 8px 4px 0;color:#22c55e;font-size:14px;">&#10003;</td><td style="padding:4px 0;color:#555;font-size:13px;">Find a quiet, well-lit, distraction-free room</td></tr>
        <tr><td style="padding:4px 8px 4px 0;color:#22c55e;font-size:14px;">&#10003;</td><td style="padding:4px 0;color:#555;font-size:13px;">Keep your resume ready</td></tr>
        <tr><td style="padding:4px 8px 4px 0;color:#22c55e;font-size:14px;">&#10003;</td><td style="padding:4px 0;color:#555;font-size:13px;">Join 5 minutes early to test setup</td></tr>
        <tr><td style="padding:4px 8px 4px 0;color:#22c55e;font-size:14px;">&#10003;</td><td style="padding:4px 0;color:#555;font-size:13px;">Close all other tabs and apps</td></tr>
      </table>
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="padding:20px 24px;background-color:#f9fafb;border-top:1px solid #eee;text-align:center;">
      <p style="color:#555;font-size:13px;margin:0 0 4px;">We wish you the very best for your interview!</p>
      <p style="color:#888;font-size:12px;margin:0;">{recruiter_name} &middot; {company_name}</p>
      {recruiter_contact_html}
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

            subject = f"Interview Invitation - {job_title} at {company_name}"

            InterviewEmailService._send_html_email(
                subject=subject,
                plain_text=plain_text,
                html_content=html_content,
                recipient=candidate_email,
            )

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
        """
        try:
            interview = Interview.objects.select_related(
                'job', 'candidate', 'candidate__user'
            ).get(id=interview_id)

            candidate_email = interview.candidate.user.email
            candidate_name = interview.candidate.user.full_name
            company_name = interview.job.company.name
            job_title = interview.job.title

            frontend_url = config('FRONTEND_URL', default='http://localhost:5173')
            interview_link = interview.meeting_link or f"{frontend_url}/interview/system-check/{interview.uuid}"
            scheduled_time = interview.scheduled_at.strftime("%B %d, %Y at %I:%M %p")

            plain_text = textwrap.dedent(f"""\
                Dear {candidate_name},

                This is a friendly reminder about your upcoming interview scheduled for tomorrow.

                Interview Details:
                Date & Time: {scheduled_time}
                Position: {job_title}
                Company: {company_name}

                Interview Link:
                {interview_link}

                Please ensure you're ready 5-10 minutes before the scheduled time.

                Good luck!

                Best regards,
                The Recruitment Team
                {company_name}
            """)

            html_content = f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f4f4f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f7;padding:20px 0;">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

  <tr>
    <td style="background:linear-gradient(135deg,#f59e0b,#ef4444);padding:28px 20px;text-align:center;">
      <h1 style="color:#ffffff;margin:0;font-size:20px;font-weight:600;">&#9200; Interview Reminder</h1>
      <p style="color:rgba(255,255,255,0.85);margin:6px 0 0;font-size:13px;">Your interview is tomorrow!</p>
    </td>
  </tr>

  <tr>
    <td style="padding:28px 24px 12px;">
      <p style="color:#333;font-size:15px;line-height:1.6;margin:0 0 20px;">Dear {candidate_name},</p>
      <p style="color:#555;font-size:14px;line-height:1.6;margin:0 0 20px;">
        This is a friendly reminder about your interview for <strong>{job_title}</strong> at <strong>{company_name}</strong>.
      </p>
    </td>
  </tr>

  <tr>
    <td style="padding:0 24px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#fffbeb;border-radius:8px;border:1px solid #fde68a;">
        <tr><td style="padding:16px 20px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="padding:4px 0;color:#b45309;font-size:13px;font-weight:600;width:120px;">Date &amp; Time</td>
              <td style="padding:4px 0;color:#333;font-size:14px;font-weight:600;">{scheduled_time}</td>
            </tr>
            <tr>
              <td style="padding:4px 0;color:#b45309;font-size:13px;font-weight:600;">Position</td>
              <td style="padding:4px 0;color:#333;font-size:14px;">{job_title}</td>
            </tr>
          </table>
        </td></tr>
      </table>
    </td>
  </tr>

  <tr>
    <td style="padding:24px;text-align:center;">
      <a href="{interview_link}" target="_blank"
         style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#f59e0b,#ef4444);color:#ffffff;text-decoration:none;border-radius:8px;font-size:15px;font-weight:600;">
        Join Interview
      </a>
    </td>
  </tr>

  <tr>
    <td style="padding:16px 24px 24px;text-align:center;">
      <p style="color:#888;font-size:13px;margin:0;">Please be ready 5-10 minutes before the scheduled time. Good luck!</p>
    </td>
  </tr>

  <tr>
    <td style="padding:16px 24px;background-color:#f9fafb;border-top:1px solid #eee;text-align:center;">
      <p style="color:#888;font-size:12px;margin:0;">The Recruitment Team &middot; {company_name}</p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

            subject = f"Reminder: Interview Tomorrow - {job_title}"

            InterviewEmailService._send_html_email(
                subject=subject,
                plain_text=plain_text,
                html_content=html_content,
                recipient=candidate_email,
            )

            return True

        except Exception as e:
            print(f"Error sending reminder email: {str(e)}")
            return False

    @staticmethod
    def send_interview_cancellation(interview_id: int, reason: str = "") -> bool:
        """
        Send cancellation email to candidate
        """
        try:
            interview = Interview.objects.select_related(
                'job', 'candidate', 'candidate__user'
            ).get(id=interview_id)

            candidate_email = interview.candidate.user.email
            candidate_name = interview.candidate.user.full_name
            company_name = interview.job.company.name
            job_title = interview.job.title

            reason_text = f"\nReason: {reason}" if reason else ""
            reason_html = f'<p style="color:#dc2626;font-size:14px;margin:12px 0;"><strong>Reason:</strong> {reason}</p>' if reason else ""

            plain_text = textwrap.dedent(f"""\
                Dear {candidate_name},

                We regret to inform you that your interview for the position of {job_title} at {company_name} has been cancelled.
                {reason_text}

                We apologize for any inconvenience this may cause. We will reach out to you if we wish to reschedule.

                Best regards,
                The Recruitment Team
                {company_name}
            """)

            html_content = f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f4f4f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f7;padding:20px 0;">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

  <tr>
    <td style="background-color:#dc2626;padding:28px 20px;text-align:center;">
      <h1 style="color:#ffffff;margin:0;font-size:20px;font-weight:600;">Interview Cancelled</h1>
      <p style="color:rgba(255,255,255,0.85);margin:6px 0 0;font-size:13px;">{job_title} at {company_name}</p>
    </td>
  </tr>

  <tr>
    <td style="padding:28px 24px;">
      <p style="color:#333;font-size:15px;line-height:1.6;margin:0 0 16px;">Dear {candidate_name},</p>
      <p style="color:#555;font-size:14px;line-height:1.6;margin:0 0 16px;">
        We regret to inform you that your interview for the position of <strong>{job_title}</strong> has been cancelled.
      </p>
      {reason_html}
      <p style="color:#555;font-size:14px;line-height:1.6;margin:16px 0 0;">
        We apologize for any inconvenience. We will reach out to you if we wish to reschedule.
      </p>
    </td>
  </tr>

  <tr>
    <td style="padding:16px 24px;background-color:#f9fafb;border-top:1px solid #eee;text-align:center;">
      <p style="color:#888;font-size:12px;margin:0;">The Recruitment Team &middot; {company_name}</p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

            subject = f"Interview Cancelled - {job_title}"

            InterviewEmailService._send_html_email(
                subject=subject,
                plain_text=plain_text,
                html_content=html_content,
                recipient=candidate_email,
            )

            return True

        except Exception as e:
            print(f"Error sending cancellation email: {str(e)}")
            return False