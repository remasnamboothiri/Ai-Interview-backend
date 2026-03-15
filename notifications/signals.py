"""
Auto-create notifications when key events happen across the platform.
All events notify recruiters, admins, and relevant candidates.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Notification
import logging

logger = logging.getLogger(__name__)


def create_notification(user, notification_type, title, message, resource_type=None, resource_id=None, action_url=None):
    """Helper to create a notification safely."""
    try:
        Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_resource_type=resource_type,
            related_resource_id=resource_id,
            action_url=action_url,
        )
        logger.info(f"📢 Notification: {notification_type} for {user.email} — {title}")
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")


def get_staff_users(exclude_user=None):
    """Get all recruiters and admins, optionally excluding one user."""
    from users.models import User
    qs = User.objects.filter(user_type__in=['recruiter', 'admin'])
    if exclude_user:
        qs = qs.exclude(id=exclude_user.id)
    return qs


def notify_staff(notification_type, title, message, resource_type=None, resource_id=None, action_url=None, exclude_user=None):
    """Notify all recruiters and admins."""
    for user in get_staff_users(exclude_user):
        create_notification(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=resource_id,
            action_url=action_url,
        )


# ═══════════════════════════════════════════════════════════════
# JOBS
# ═══════════════════════════════════════════════════════════════
@receiver(post_save, sender='jobs.Job')
def notify_job_event(sender, instance, created, **kwargs):
    try:
        if created:
            notify_staff(
                notification_type='job_created',
                title='New Job Created',
                message=f'Job "{instance.title}" has been created.',
                resource_type='job',
                resource_id=instance.id,
                action_url=f'/jobs/{instance.id}',
            )
        else:
            status = getattr(instance, 'status', None)
            if status == 'closed':
                notify_staff(
                    notification_type='job_updated',
                    title='Job Closed',
                    message=f'Job "{instance.title}" has been closed.',
                    resource_type='job',
                    resource_id=instance.id,
                    action_url=f'/jobs/{instance.id}',
                )
    except Exception as e:
        logger.error(f"Job notification error: {e}")


@receiver(post_delete, sender='jobs.Job')
def notify_job_deleted(sender, instance, **kwargs):
    try:
        notify_staff(
            notification_type='job_updated',
            title='Job Deleted',
            message=f'Job "{instance.title}" has been deleted.',
            resource_type='job',
        )
    except Exception as e:
        logger.error(f"Job delete notification error: {e}")


# ═══════════════════════════════════════════════════════════════
# CANDIDATES
# ═══════════════════════════════════════════════════════════════
@receiver(post_save, sender='candidates.Candidate')
def notify_candidate_event(sender, instance, created, **kwargs):
    try:
        if not created:
            return

        candidate_user = getattr(instance, 'user', None)

        # Notify the candidate themselves
        if candidate_user:
            create_notification(
                user=candidate_user,
                notification_type='candidate_registered',
                title='Welcome to HireFlow',
                message='Your candidate profile has been created. You will receive interview invitations here.',
                resource_type='candidate',
                resource_id=instance.id,
                action_url='/profile',
            )

        # Notify all recruiters and admins
        name = 'New candidate'
        if candidate_user:
            name = getattr(candidate_user, 'full_name', '') or getattr(candidate_user, 'email', 'New candidate')

        notify_staff(
            notification_type='candidate_added',
            title='New Candidate Added',
            message=f'Candidate "{name}" has been added to the system.',
            resource_type='candidate',
            resource_id=instance.id,
            action_url=f'/candidates/{instance.id}',
            exclude_user=candidate_user,
        )
    except Exception as e:
        logger.error(f"Candidate notification error: {e}")


@receiver(post_delete, sender='candidates.Candidate')
def notify_candidate_deleted(sender, instance, **kwargs):
    try:
        candidate_user = getattr(instance, 'user', None)
        name = 'Unknown'
        if candidate_user:
            name = getattr(candidate_user, 'full_name', '') or getattr(candidate_user, 'email', 'Unknown')

        notify_staff(
            notification_type='candidate_added',
            title='Candidate Removed',
            message=f'Candidate "{name}" has been removed from the system.',
            resource_type='candidate',
        )
    except Exception as e:
        logger.error(f"Candidate delete notification error: {e}")


# ═══════════════════════════════════════════════════════════════
# INTERVIEWS
# ═══════════════════════════════════════════════════════════════
@receiver(post_save, sender='interviews.Interview')
def notify_interview_event(sender, instance, created, **kwargs):
    try:
        candidate_user = None
        candidate_name = 'Candidate'
        if hasattr(instance, 'candidate') and instance.candidate:
            candidate_user = getattr(instance.candidate, 'user', None)
            if candidate_user:
                candidate_name = getattr(candidate_user, 'full_name', '') or getattr(candidate_user, 'email', 'Candidate')

        job_title = 'Position'
        if hasattr(instance, 'job') and instance.job:
            job_title = instance.job.title

        if created:
            notify_staff(
                notification_type='interview_scheduled',
                title='Interview Scheduled',
                message=f'Interview for {candidate_name} — {job_title} has been scheduled.',
                resource_type='interview',
                resource_id=instance.id,
                action_url=f'/interviews/{instance.id}',
            )
            if candidate_user:
                create_notification(
                    user=candidate_user,
                    notification_type='interview_scheduled',
                    title='Interview Scheduled',
                    message=f'You have been scheduled for an interview for the {job_title} position.',
                    resource_type='interview',
                    resource_id=instance.id,
                    action_url=f'/interview-room/{instance.uuid}',
                )
        else:
            status = getattr(instance, 'status', '')

            if status == 'completed':
                notify_staff(
                    notification_type='interview_completed',
                    title='Interview Completed',
                    message=f'{candidate_name} has completed the interview for {job_title}.',
                    resource_type='interview',
                    resource_id=instance.id,
                    action_url=f'/interviews/{instance.id}',
                )

            elif status == 'cancelled':
                notify_staff(
                    notification_type='interview_cancelled',
                    title='Interview Cancelled',
                    message=f'Interview for {candidate_name} — {job_title} has been cancelled.',
                    resource_type='interview',
                    resource_id=instance.id,
                    action_url=f'/interviews/{instance.id}',
                )
                if candidate_user:
                    create_notification(
                        user=candidate_user,
                        notification_type='interview_cancelled',
                        title='Interview Cancelled',
                        message=f'Your interview for {job_title} has been cancelled.',
                        resource_type='interview',
                        resource_id=instance.id,
                    )

            elif status == 'in_progress':
                notify_staff(
                    notification_type='interview_started',
                    title='Interview In Progress',
                    message=f'{candidate_name} has started the interview for {job_title}.',
                    resource_type='interview',
                    resource_id=instance.id,
                    action_url=f'/interviews/{instance.id}',
                )
    except Exception as e:
        logger.error(f"Interview notification error: {e}")


@receiver(post_delete, sender='interviews.Interview')
def notify_interview_deleted(sender, instance, **kwargs):
    try:
        job_title = 'Position'
        if hasattr(instance, 'job') and instance.job:
            job_title = instance.job.title

        notify_staff(
            notification_type='interview_cancelled',
            title='Interview Deleted',
            message=f'Interview for {job_title} has been deleted.',
            resource_type='interview',
        )
    except Exception as e:
        logger.error(f"Interview delete notification error: {e}")


# ═══════════════════════════════════════════════════════════════
# INTERVIEW RESULTS
# ═══════════════════════════════════════════════════════════════
@receiver(post_save, sender='interview_results.InterviewResult')
def notify_result_event(sender, instance, created, **kwargs):
    try:
        if not created:
            return

        interview = instance.interview

        candidate_name = 'Candidate'
        if hasattr(interview, 'candidate') and interview.candidate:
            cuser = getattr(interview.candidate, 'user', None)
            if cuser:
                candidate_name = getattr(cuser, 'full_name', '') or getattr(cuser, 'email', 'Candidate')

        job_title = 'Position'
        if hasattr(interview, 'job') and interview.job:
            job_title = interview.job.title

        score = instance.overall_score
        passed = getattr(instance, 'passed', None)
        recommendation = getattr(instance, 'recommendation', 'N/A')
        status_text = ''
        if passed is True:
            status_text = 'Passed ✓'
        elif passed is False:
            status_text = 'Not Passed ✗'

        notify_staff(
            notification_type='result_available',
            title='Interview Result Available',
            message=f'Result for {candidate_name} — {job_title}: Score {score}/10. {status_text} Recommendation: {recommendation}.',
            resource_type='interview_result',
            resource_id=instance.id,
            action_url=f'/results/{interview.id}',
        )
    except Exception as e:
        logger.error(f"Result notification error: {e}")


# ═══════════════════════════════════════════════════════════════
# AI AGENTS
# ═══════════════════════════════════════════════════════════════
@receiver(post_save, sender='agents.Agent')
def notify_agent_event(sender, instance, created, **kwargs):
    try:
        if not created:
            return

        notify_staff(
            notification_type='agent_created',
            title='AI Agent Created',
            message=f'AI Agent "{instance.name}" ({instance.interview_type}) has been created.',
            resource_type='agent',
            resource_id=instance.id,
            action_url=f'/ai-agents/{instance.id}',
        )
    except Exception as e:
        logger.error(f"Agent notification error: {e}")


@receiver(post_delete, sender='agents.Agent')
def notify_agent_deleted(sender, instance, **kwargs):
    try:
        notify_staff(
            notification_type='agent_created',
            title='AI Agent Deleted',
            message=f'AI Agent "{instance.name}" has been deleted.',
            resource_type='agent',
        )
    except Exception as e:
        logger.error(f"Agent delete notification error: {e}")


# ═══════════════════════════════════════════════════════════════
# JOB APPLICATIONS
# ═══════════════════════════════════════════════════════════════
@receiver(post_save, sender='job_applications.JobApplication')
def notify_application_event(sender, instance, created, **kwargs):
    try:
        job_title = 'Position'
        if hasattr(instance, 'job') and instance.job:
            job_title = instance.job.title

        candidate_user = None
        candidate_name = 'Candidate'
        if hasattr(instance, 'candidate') and instance.candidate:
            candidate_user = getattr(instance.candidate, 'user', None)
            if candidate_user:
                candidate_name = getattr(candidate_user, 'full_name', '') or getattr(candidate_user, 'email', 'Candidate')

        if created:
            notify_staff(
                notification_type='application_received',
                title='New Application Received',
                message=f'{candidate_name} has applied for {job_title}.',
                resource_type='application',
                resource_id=instance.id,
                action_url=f'/applications/{instance.id}',
            )
            if candidate_user:
                create_notification(
                    user=candidate_user,
                    notification_type='application_received',
                    title='Application Submitted',
                    message=f'Your application for {job_title} has been submitted successfully.',
                    resource_type='application',
                    resource_id=instance.id,
                )
        else:
            app_status = getattr(instance, 'status', '')
            if app_status and candidate_user:
                create_notification(
                    user=candidate_user,
                    notification_type='application_status_changed',
                    title='Application Status Updated',
                    message=f'Your application for {job_title} status: {app_status.replace("_", " ").title()}.',
                    resource_type='application',
                    resource_id=instance.id,
                )
    except Exception as e:
        logger.error(f"Application notification error: {e}")