"""
Interview Result Generator
Auto-generates InterviewResult after interview completes by using
Gemini AI to evaluate the conversation transcript.
"""

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

    # Use AI to evaluate
    try:
        evaluation = _evaluate_with_ai(interview, transcript)
    except Exception as e:
        logger.error(f"AI evaluation failed for interview {interview_id}: {e}")
        evaluation = _default_evaluation()

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
        ai_feedback=evaluation.get('ai_feedback', {}),
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


def _evaluate_with_ai(interview, transcript: str) -> dict:
    """Use Gemini to evaluate the interview transcript."""
    genai.configure(api_key=config('GEMINI_API_KEY'))

    job = interview.job
    candidate = interview.candidate

    prompt = f"""You are an expert interview evaluator. Analyze the following interview transcript and provide a detailed evaluation.

**Job Details:**
- Position: {job.title}
- Experience Level: {job.experience_level}
- Required Skills: {', '.join(job.skills_required) if job.skills_required else 'Not specified'}

**Candidate:**
- Name: {candidate.user.full_name}
- Experience: {candidate.experience_years} years

**Interview Transcript:**
{transcript}

**Evaluate and respond with ONLY valid JSON (no markdown, no code blocks):**
{{
    "overall_score": <number 1-10>,
    "technical_score": <number 1-10>,
    "communication_score": <number 1-10>,
    "cultural_fit_score": <number 1-10>,
    "behavioral_score": <number 1-10>,
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "red_flags": ["red flag if any, or empty array"],
    "recommendation": "<hire|reject|maybe|second_round>",
    "interview_quality": <number 1-10>,
    "technical_depth": <number 1-10>,
    "behavioral_analysis": {{
        "confidence_level": "<high|medium|low>",
        "engagement": "<high|medium|low>",
        "clarity": "<high|medium|low>"
    }},
    "skill_assessment": {{
        "relevant_skills_demonstrated": ["skill1", "skill2"],
        "missing_skills": ["skill1"]
    }},
    "ai_feedback": {{
        "summary": "2-3 sentence overall assessment",
        "hiring_justification": "1-2 sentence justification for the recommendation"
    }}
}}

Score Guidelines:
- 8-10: Excellent candidate, strong hire
- 6-7: Good candidate, potential hire
- 4-5: Average, needs further evaluation
- 1-3: Below expectations, likely reject

Be fair and objective. Base scores ONLY on what the candidate actually said."""

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            max_output_tokens=1000,
        )
    )

    response = model.generate_content(prompt)
    text = response.text.strip()

    # Clean up response — remove markdown code blocks if present
    if text.startswith('```'):
        text = text.split('\n', 1)[1] if '\n' in text else text[3:]
    if text.endswith('```'):
        text = text[:-3]
    text = text.strip()

    try:
        evaluation = json.loads(text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse AI evaluation: {text[:200]}")
        evaluation = _default_evaluation()

    # Clamp scores to valid range
    for key in ['overall_score', 'technical_score', 'communication_score',
                'cultural_fit_score', 'behavioral_score']:
        if key in evaluation:
            evaluation[key] = max(1.0, min(10.0, float(evaluation[key])))

    for key in ['interview_quality', 'technical_depth']:
        if key in evaluation:
            evaluation[key] = max(1, min(10, int(evaluation[key])))

    # Validate recommendation
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
        'strengths': ['Completed the interview'],
        'weaknesses': ['Unable to fully evaluate - AI scoring unavailable'],
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
            'summary': 'Interview completed. Manual review recommended as AI scoring was unavailable.',
            'hiring_justification': 'Recommend manual review of the transcript.'
        }
    }


def _create_empty_result(interview, user=None) -> InterviewResult:
    """Create a minimal result when no conversation exists."""
    evaluation = _default_evaluation()
    evaluation['weaknesses'] = ['No conversation data recorded']
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
        weaknesses=evaluation['weaknesses'],
        red_flags=['No conversation data'],
        recommendation='maybe',
        transcript='No conversation recorded.',
        ai_feedback=evaluation['ai_feedback'],
        recruiter_feedback='',
        interview_quality=0,
        technical_depth=0,
        result_generated_at=timezone.now(),
        created_by=user if user and hasattr(user, 'pk') and user.pk else None,
    )