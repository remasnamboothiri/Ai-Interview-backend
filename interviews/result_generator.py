"""
Interview Result Generator
Auto-generates InterviewResult after interview completes by using
Gemini AI to evaluate the conversation transcript.
Now includes screenshot analysis and cheating detection.
"""
import os  
import google.generativeai as genai
import json
import logging
from decimal import Decimal
from django.utils import timezone
from decouple import config
from interview_data.models import InterviewConversation
from interview_results.models import InterviewResult
from .models import Interview

logger = logging.getLogger(__name__)


def generate_interview_result(interview_id: int, user=None) -> InterviewResult:
    """
    Generate an InterviewResult by analyzing the conversation with AI.
    Called automatically when an interview is completed.
    """
    interview = Interview.objects.select_related(
        'job', 'candidate', 'candidate__user', 'agent'
    ).get(id=interview_id)

    # Check if result already exists
    existing = InterviewResult.objects.filter(interview=interview).first()
    if existing:
        logger.info(f"Result already exists for interview {interview_id}")
        return existing

    # Get full conversation transcript
    conversations = InterviewConversation.objects.filter(
        interview=interview
    ).order_by('timestamp')

    if not conversations.exists():
        logger.warning(f"No conversation data for interview {interview_id}")
        return _create_empty_result(interview, user)

    # Build transcript
    transcript_lines = []
    questions_asked = []
    for conv in conversations:
        speaker = "AI Interviewer" if conv.speaker == 'ai' else "Candidate"
        transcript_lines.append(f"{speaker}: {conv.message}")
        if conv.speaker == 'ai':
            questions_asked.append(conv.message)

    transcript = "\n\n".join(transcript_lines)

    # Get screenshots for cheating detection
    screenshot_analysis = _analyze_screenshots(interview_id)

    # Use AI to evaluate transcript
    try:
        evaluation = _evaluate_with_ai(interview, transcript, screenshot_analysis)
    except Exception as e:
        logger.error(f"AI evaluation failed for interview {interview_id}: {e}")
        logger.exception("Full traceback:")
        evaluation = _default_evaluation()

    # Merge cheating flags into red_flags
    if screenshot_analysis.get('cheating_detected'):
        cheating_flags = screenshot_analysis.get('cheating_flags', [])
        existing_flags = evaluation.get('red_flags', [])
        evaluation['red_flags'] = existing_flags + cheating_flags

        # If cheating detected, override recommendation to reject
        if screenshot_analysis.get('severity') == 'high':
            evaluation['recommendation'] = 'reject'
            evaluation['overall_score'] = min(
                float(evaluation.get('overall_score', 5.0)), 3.0
            )

    # Create the result
    result = InterviewResult.objects.create(
        interview=interview,
        overall_score=Decimal(str(evaluation.get('overall_score', 5.0))),
        technical_score=Decimal(str(evaluation.get('technical_score', 5.0))),
        communication_score=Decimal(str(evaluation.get('communication_score', 5.0))),
        cultural_fit_score=Decimal(str(evaluation.get('cultural_fit_score', 5.0))),
        behavioral_score=Decimal(str(evaluation.get('behavioral_score', 5.0))),
        questions_asked=questions_asked,
        response_times=[],
        behavioral_analysis=evaluation.get('behavioral_analysis', {}),
        skill_assessment=evaluation.get('skill_assessment', {}),
        strengths=evaluation.get('strengths', []),
        weaknesses=evaluation.get('weaknesses', []),
        red_flags=evaluation.get('red_flags', []),
        recommendation=evaluation.get('recommendation', 'maybe'),
        transcript=transcript,
        ai_feedback={
            **evaluation.get('ai_feedback', {}),
            'screenshot_analysis': screenshot_analysis,
        },
        recruiter_feedback='',
        interview_quality=evaluation.get('interview_quality', 5),
        technical_depth=evaluation.get('technical_depth', 5),
        result_generated_at=timezone.now(),
        created_by=user if user and hasattr(user, 'pk') and user.pk else None,
    )

    logger.info(
        f"Result generated for interview {interview_id}: "
        f"score={result.overall_score}, recommendation={result.recommendation}"
    )
    return result


def _analyze_screenshots(interview_id: int) -> dict:
    """
    Analyze screenshots for cheating detection using Gemini Vision.
    """
    try:
        from interview_screenshots.models import InterviewScreenshot

        screenshots = InterviewScreenshot.objects.filter(
            interview_id=interview_id
        ).order_by('created_at')

        total = screenshots.count()
        logger.info(f"Found {total} screenshots for interview {interview_id}")

        if total == 0:
            return {
                'cheating_detected': False,
                'cheating_flags': [],
                'total_screenshots': total,
                'note': 'No screenshots captured during interview'
            }

        genai.configure(api_key=config('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-2.5-flash')  # ✅ Changed from 1.5-flash

        cheating_flags = []
        screenshot_urls = []
        multiple_person_count = 0
        phone_detected_count = 0
        looking_away_count = 0

        # Pick up to 10 evenly spaced screenshots
        step = max(1, total // 10)
        screenshots_to_analyze = list(screenshots)[::step][:10]
        analyzed_count = 0

        for screenshot in screenshots_to_analyze:
            try:
                file_url = screenshot.screenshot_url
                if not file_url:
                    continue

                screenshot_urls.append(file_url)

                from django.conf import settings
                relative_path = file_url.lstrip('/')
                if relative_path.startswith('media/'):
                    relative_path = relative_path[6:]
                file_path = os.path.join(settings.MEDIA_ROOT, relative_path)

                if not os.path.exists(file_path):
                    logger.warning(f"Screenshot file not found: {file_path}")
                    continue

                import base64
                with open(file_path, 'rb') as f:
                    image_data = f.read()

                image_part = {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(image_data).decode()
                }

                prompt = """Analyze this interview webcam screenshot carefully.
Check for these specific issues:
1. Are there multiple people visible (not just the candidate)?
2. Is a phone or mobile device visible or being used?
3. Is the candidate clearly looking away from the screen for a long time?
4. Is the candidate absent or is the camera blocked?

Respond ONLY with this exact JSON format:
{
    "multiple_persons": true or false,
    "phone_detected": true or false,
    "looking_away": true or false,
    "not_present": true or false,
    "notes": "one sentence describing what you see"
}"""

                response = model.generate_content([prompt, image_part])
                text = response.text.strip()

                # Clean JSON markers
                if '```' in text:
                    text = text.split('```')[1] if '```' in text else text
                    if text.startswith('json'):
                        text = text[4:]
                text = text.strip()

                analysis = json.loads(text)
                analyzed_count += 1

                if analysis.get('multiple_persons'):
                    multiple_person_count += 1
                if analysis.get('phone_detected'):
                    phone_detected_count += 1
                if analysis.get('looking_away'):
                    looking_away_count += 1

                logger.info(f"Screenshot analyzed: {analysis.get('notes', '')}")

            except Exception as e:
                logger.warning(f"Could not analyze screenshot {screenshot.id}: {e}")
                continue

        # Determine cheating flags
        if multiple_person_count >= 2:
            cheating_flags.append(
                f"Multiple people detected in {multiple_person_count} screenshots — "
                f"possible external assistance"
            )
        if phone_detected_count >= 1:
            cheating_flags.append(
                f"Mobile phone detected in {phone_detected_count} screenshots — "
                f"possible use of external resources"
            )
        if looking_away_count >= 3:
            cheating_flags.append(
                f"Candidate looking away from screen in {looking_away_count} screenshots — "
                f"possible reading from external material"
            )

        cheating_detected = len(cheating_flags) > 0
        severity = 'high' if len(cheating_flags) >= 2 else ('medium' if cheating_flags else 'none')

        return {
            'cheating_detected': cheating_detected,
            'severity': severity,
            'cheating_flags': cheating_flags,
            'total_screenshots': total,
            'screenshots_analyzed': analyzed_count,
            'screenshot_urls': screenshot_urls[:5],
            'multiple_person_count': multiple_person_count,
            'phone_detected_count': phone_detected_count,
            'looking_away_count': looking_away_count,
        }

    except Exception as e:
        logger.error(f"Screenshot analysis failed: {e}")
        logger.exception("Full traceback:")
        return {
            'cheating_detected': False,
            'cheating_flags': [],
            'total_screenshots': 0,
            'error': str(e)
        }


def _evaluate_with_ai(interview, transcript: str, screenshot_analysis: dict = None) -> dict:
    """Use Gemini to evaluate the interview transcript."""
    genai.configure(api_key=config('GEMINI_API_KEY'))

    job = interview.job
    candidate = interview.candidate

    # Include cheating context in prompt if detected
    cheating_context = ""
    if screenshot_analysis and screenshot_analysis.get('cheating_detected'):
        cheating_context = f"""
**IMPORTANT — Integrity Issues Detected:**
The following issues were detected via screenshot analysis:
{chr(10).join(f"- {flag}" for flag in screenshot_analysis.get('cheating_flags', []))}
Please factor these integrity concerns into your evaluation.
"""

    prompt = f"""You are an expert interview evaluator. Analyze the following interview transcript and provide a detailed evaluation.

**Job Details:**
- Position: {job.title}
- Experience Level: {job.experience_level}
- Required Skills: {', '.join(job.skills_required) if job.skills_required else 'Not specified'}

**Candidate:**
- Name: {candidate.user.full_name}
- Experience: {candidate.experience_years} years

{cheating_context}

**Interview Transcript:**
{transcript}

**IMPORTANT INSTRUCTIONS:**
- Evaluate EACH candidate individually based on their actual answers
- Do NOT use generic responses
- Base scores ONLY on what THIS candidate actually said
- Be specific about their actual strengths and weaknesses
- If transcript is short, note that but still evaluate what was said

**Evaluate and respond with ONLY valid JSON (no markdown, no code blocks):**
{{
    "overall_score": <number 1-10>,
    "technical_score": <number 1-10>,
    "communication_score": <number 1-10>,
    "cultural_fit_score": <number 1-10>,
    "behavioral_score": <number 1-10>,
    "strengths": ["specific strength from their actual answers", "another specific strength"],
    "weaknesses": ["specific area they need to improve based on their answers"],
    "red_flags": ["any concerns, or empty array if none"],
    "recommendation": "<hire|reject|maybe|second_round>",
    "interview_quality": <number 1-10>,
    "technical_depth": <number 1-10>,
    "behavioral_analysis": {{
        "confidence_level": "<high|medium|low>",
        "engagement": "<high|medium|low>",
        "clarity": "<high|medium|low>"
    }},
    "skill_assessment": {{
        "relevant_skills_demonstrated": ["actual skills they showed"],
        "missing_skills": ["skills needed but not demonstrated"]
    }},
    "ai_feedback": {{
        "summary": "2-3 sentence assessment specific to THIS candidate's performance",
        "hiring_justification": "1-2 sentence justification based on their actual answers"
    }}
}}

Score Guidelines:
- 8-10: Excellent candidate, strong hire
- 6-7: Good candidate, potential hire
- 4-5: Average, needs further evaluation
- 1-3: Below expectations, likely reject"""

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",  # ✅ Changed from 1.5-flash
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            max_output_tokens=8000,
        )
    )

    response = model.generate_content(prompt)
    text = response.text.strip()

    # Clean up response
    if text.startswith('```'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:]) if len(lines) > 1 else text[3:]
    if text.endswith('```'):
        text = text[:-3]
    text = text.strip()

    # Log raw response for debugging
    logger.info(f"Gemini raw response (first 300 chars): {text[:300]}")

    try:
        evaluation = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI evaluation JSON: {e}")
        logger.error(f"Raw text: {text[:500]}")
        raise  # Re-raise so caller can use fallback

    # Clamp scores
    for key in ['overall_score', 'technical_score', 'communication_score',
                'cultural_fit_score', 'behavioral_score']:
        if key in evaluation:
            evaluation[key] = max(1.0, min(10.0, float(evaluation[key])))

    for key in ['interview_quality', 'technical_depth']:
        if key in evaluation:
            evaluation[key] = max(1, min(10, int(evaluation[key])))

    valid_recs = ['hire', 'reject', 'maybe', 'second_round']
    if evaluation.get('recommendation') not in valid_recs:
        evaluation['recommendation'] = 'maybe'

    return evaluation


def _default_evaluation() -> dict:
    """Fallback evaluation if AI fails."""
    return {
        'overall_score': 5.0,
        'technical_score': 5.0,
        'communication_score': 5.0,
        'cultural_fit_score': 5.0,
        'behavioral_score': 5.0,
        'strengths': [],
        'weaknesses': [],
        'red_flags': [],
        'recommendation': 'maybe',
        'interview_quality': 5,
        'technical_depth': 5,
        'behavioral_analysis': {
            'confidence_level': 'medium',
            'engagement': 'medium',
            'clarity': 'medium'
        },
        'skill_assessment': {
            'relevant_skills_demonstrated': [],
            'missing_skills': []
        },
        'ai_feedback': {
            'summary': 'AI evaluation could not be completed. Please review the transcript manually.',
            'hiring_justification': 'Manual review of transcript recommended.'
        }
    }


def _create_empty_result(interview, user=None) -> InterviewResult:
    """Create a minimal result when no conversation exists."""
    evaluation = _default_evaluation()
    evaluation['red_flags'] = ['No conversation data recorded']
    evaluation['recommendation'] = 'maybe'

    return InterviewResult.objects.create(
        interview=interview,
        overall_score=Decimal('0.0'),
        technical_score=Decimal('0.0'),
        communication_score=Decimal('0.0'),
        cultural_fit_score=Decimal('0.0'),
        behavioral_score=Decimal('0.0'),
        questions_asked=[],
        response_times=[],
        behavioral_analysis=evaluation['behavioral_analysis'],
        skill_assessment=evaluation['skill_assessment'],
        strengths=[],
        weaknesses=[],
        red_flags=evaluation['red_flags'],
        recommendation='maybe',
        transcript='No conversation recorded.',
        ai_feedback=evaluation['ai_feedback'],
        recruiter_feedback='',
        interview_quality=0,
        technical_depth=0,
        result_generated_at=timezone.now(),
        created_by=user if user and hasattr(user, 'pk') and user.pk else None,
    )