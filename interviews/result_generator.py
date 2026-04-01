"""
Interview Result Generator
Auto-generates InterviewResult after interview completes.
Uses DeepSeek AI via LangChain for transcript evaluation.
Screenshot analysis uses client-side detection metadata (no vision API needed).

Requires: pip install langchain-openai
Env var:  DEEPSEEK_API_KEY=your-deepseek-api-key
"""
import json
import logging
from decimal import Decimal
from django.utils import timezone
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
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

    # Analyze screenshots using client-side metadata (no vision API)
    screenshot_analysis = _analyze_screenshots_from_metadata(interview_id)

    # Use DeepSeek via LangChain to evaluate transcript
    try:
        evaluation = _evaluate_with_deepseek(interview, transcript, screenshot_analysis)
    except Exception as e:
        logger.error(f"AI evaluation failed for interview {interview_id}: {e}")
        logger.exception("Full traceback:")
        evaluation = _default_evaluation()

    # Merge cheating flags into red_flags
    if screenshot_analysis.get('cheating_detected'):
        cheating_flags = screenshot_analysis.get('cheating_flags', [])
        existing_flags = evaluation.get('red_flags', [])
        evaluation['red_flags'] = existing_flags + cheating_flags

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


def _analyze_screenshots_from_metadata(interview_id: int) -> dict:
    """
    Analyze screenshots using client-side detection metadata.
    No vision API needed — reads face_count, issue_type, and metadata
    fields that were set by the frontend during the interview.
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
                'total_screenshots': 0,
                'screenshots_analyzed': 0,
                'screenshot_urls': [],
                'multiple_person_count': 0,
                'phone_detected_count': 0,
                'looking_away_count': 0,
                'camera_off_count': 0,
                'note': 'No screenshots captured during interview',
            }

        flagged_urls = []
        normal_urls = []
        multiple_person_count = 0
        phone_detected_count = 0
        looking_away_count = 0
        camera_off_count = 0  # ← NEW: track camera-off screenshots

        for ss in screenshots:
            # Parse metadata once
            meta = ss.metadata if isinstance(ss.metadata, dict) else {}
            if isinstance(ss.metadata, str):
                try:
                    meta = json.loads(ss.metadata)
                except (json.JSONDecodeError, TypeError):
                    meta = {}

            issue = ss.issue_type or ''

            # Count multiple faces (from face-api.js detection)
            if ss.face_count and ss.face_count > 1:
                multiple_person_count += 1
            elif ss.multiple_people_detected:
                multiple_person_count += 1

            # Count once per screenshot (prevent double-counting from metadata + issue_type)
            phone_from_meta = meta.get('phone_detected', False)
            phone_from_issue = 'phone' in issue.lower()
            if phone_from_meta or phone_from_issue:
                phone_detected_count += 1

            looking_from_meta = meta.get('looking_away', False)
            looking_from_issue = 'looking_away' in issue.lower() or 'gaze' in issue.lower()
            if looking_from_meta or looking_from_issue:
                looking_away_count += 1

            # ── NEW: Camera off detection ──────────────────────────
            camera_off_from_meta = meta.get('camera_off', False)
            camera_off_from_issue = 'camera_off' in issue.lower()
            if camera_off_from_meta or camera_off_from_issue:
                camera_off_count += 1

            # Separate flagged vs normal screenshots for display
            if ss.screenshot_url:
                has_issue = (
                    getattr(ss, 'is_flagged', False) or
                    (ss.face_count and ss.face_count > 1) or
                    phone_from_meta or phone_from_issue or
                    looking_from_meta or looking_from_issue or
                    camera_off_from_meta or camera_off_from_issue  # ← NEW
                )
                if has_issue:
                    flagged_urls.append(ss.screenshot_url)
                else:
                    normal_urls.append(ss.screenshot_url)

        # Show flagged screenshots first, fill remaining with normal ones
        screenshot_urls = flagged_urls[:5]
        if len(screenshot_urls) < 5:
            screenshot_urls += normal_urls[:5 - len(screenshot_urls)]

        # Build cheating flags
        cheating_flags = []

        if multiple_person_count >= 2:
            cheating_flags.append(
                f"Multiple people detected in {multiple_person_count} screenshots "
                f"— possible external assistance"
            )
        if phone_detected_count >= 1:
            cheating_flags.append(
                f"Mobile phone detected in {phone_detected_count} screenshots "
                f"— possible use of external resources"
            )
        if looking_away_count >= 3:
            cheating_flags.append(
                f"Candidate looking away in {looking_away_count} screenshots "
                f"— possible reading from external material"
            )
        # ── NEW: Camera off flag ───────────────────────────────────
        if camera_off_count >= 2:
            cheating_flags.append(
                f"Candidate disabled camera in {camera_off_count} screenshots "
                f"— video was intentionally turned off during the interview"
            )

        cheating_detected = len(cheating_flags) > 0
        severity = 'high' if len(cheating_flags) >= 2 else ('medium' if cheating_flags else 'none')

        return {
            'cheating_detected': cheating_detected,
            'severity': severity,
            'cheating_flags': cheating_flags,
            'total_screenshots': total,
            'screenshots_analyzed': total,
            'screenshot_urls': screenshot_urls,
            'multiple_person_count': multiple_person_count,
            'phone_detected_count': phone_detected_count,
            'looking_away_count': looking_away_count,
            'camera_off_count': camera_off_count,  # ← NEW
        }

    except Exception as e:
        logger.error(f"Screenshot metadata analysis failed: {e}")
        logger.exception("Full traceback:")
        return {
            'cheating_detected': False,
            'cheating_flags': [],
            'total_screenshots': 0,
            'camera_off_count': 0,
            'error': str(e),
        }


def _evaluate_with_deepseek(interview, transcript: str, screenshot_analysis: dict = None) -> dict:
    """Use DeepSeek via LangChain to evaluate the interview transcript."""
    llm = ChatOpenAI(
        model=config('DEEPSEEK_MODEL'),
        api_key=config('DEEPSEEK_API_KEY'),
        base_url=config('DEEPSEEK_BASE_URL'),
        temperature=float(config('DEEPSEEK_EVAL_TEMPERATURE')),
        max_tokens=int(config('DEEPSEEK_EVAL_MAX_TOKENS')),
    )

    job = interview.job
    candidate = interview.candidate

    # Include cheating context in prompt if detected
    cheating_context = ""
    if screenshot_analysis and screenshot_analysis.get('cheating_detected'):
        cheating_context = f"""
**IMPORTANT — Integrity Issues Detected:**
The following issues were detected via automated monitoring:
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

**CRITICAL — ASR TRANSCRIPT NOTICE:**
This transcript was captured via voice recognition (speech-to-text) and may contain:
- Misheared words or garbled phrases
- Incorrect names (e.g. "Abana Patmohama" may actually mean "Aparna Padmakumar")
- Technical terms spelled phonetically
- Grammar errors caused by transcription, not by the candidate

DO NOT penalize candidates for transcription errors. Judge the SUBSTANCE and INTENT
of answers, not surface-level spelling or phrasing. If an answer seems garbled but
the topic is clearly relevant, assume the candidate answered correctly and score accordingly.

**IMPORTANT SCORING RULES:**
- 1-2: Candidate gave NO substantive answers at all — complete silence or total irrelevance
- 3-4: Partial engagement — some answers but missing key depth
- 5-6: Adequate answers — addressed the questions reasonably
- 7-8: Good answers — demonstrated relevant knowledge and experience
- 9-10: Excellent — exceptional depth and clarity
- If the candidate attempted to answer ALL questions with relevant content, minimum score is 5
- NEVER score below 4 if there are 3 or more substantive candidate responses in the transcript

**IMPORTANT INSTRUCTIONS:**
- Evaluate based on the candidate's actual answers
- Do NOT use generic responses
- Be specific about their actual strengths and weaknesses
- If transcript is short, note that but still evaluate what was said

**Respond with ONLY valid JSON (no markdown, no code blocks):**
{{
    "overall_score": <number 1-10>,
    "technical_score": <number 1-10>,
    "communication_score": <number 1-10>,
    "cultural_fit_score": <number 1-10>,
    "behavioral_score": <number 1-10>,
    "strengths": ["specific strength from their answers"],
    "weaknesses": ["specific area to improve"],
    "red_flags": ["concerns, or empty array"],
    "recommendation": "<hire|reject|maybe|second_round>",
    "interview_quality": <number 1-10>,
    "technical_depth": <number 1-10>,
    "behavioral_analysis": {{
        "confidence_level": "<high|medium|low>",
        "engagement": "<high|medium|low>",
        "clarity": "<high|medium|low>"
    }},
    "skill_assessment": {{
        "relevant_skills_demonstrated": ["skills shown"],
        "missing_skills": ["skills not demonstrated"]
    }},
    "ai_feedback": {{
        "summary": "2-3 sentence assessment of THIS candidate",
        "hiring_justification": "1-2 sentence justification"
    }}
}}

Score Guidelines:
- 8-10: Excellent, strong hire
- 6-7: Good, potential hire
- 4-5: Average, needs further evaluation
- 1-3: Below expectations, likely reject"""

    messages = [
        SystemMessage(content="You are an expert interview evaluator. Always respond with valid JSON only, no markdown."),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    text = response.content.strip()

    # Clean up response (remove markdown code fences if present)
    if text.startswith('```'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:]) if len(lines) > 1 else text[3:]
    if text.endswith('```'):
        text = text[:-3]
    text = text.strip()

    logger.info(f"DeepSeek raw response (first 300 chars): {text[:300]}")

    try:
        evaluation = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI evaluation JSON: {e}")
        logger.error(f"Raw text: {text[:500]}")
        raise

    # ── ASR safety floor ──────────────────────────────────────────
    # Prevent garbage scoring when the candidate clearly engaged.
    # Counts substantive candidate turns (10+ words) from the transcript.
    # If 3+ substantive turns exist, floor all scores at 4.0 and strip
    # false "no engagement" weaknesses that ASR errors can cause.
    candidate_lines = [
        line for line in transcript.split('\n\n')
        if line.startswith('Candidate:') and len(line.split()) >= 10
    ]
    substantive_turns = len(candidate_lines)

    if substantive_turns >= 3:
        for score_key in ['overall_score', 'technical_score', 'communication_score',
                          'cultural_fit_score', 'behavioral_score']:
            if score_key in evaluation:
                current = float(evaluation[score_key])
                evaluation[score_key] = max(current, 4.0)

        # Remove false "no engagement" weaknesses
        evaluation['weaknesses'] = [
            w for w in evaluation.get('weaknesses', [])
            if not any(phrase in w.lower() for phrase in [
                'no answer', 'failed to engage', 'no technical',
                'no demonstration', 'no behavioral', 'did not answer',
                'no response', 'no engagement',
            ])
        ]

        # Fix recommendation if it's reject but score is now 4+
        if (evaluation.get('recommendation') == 'reject'
                and float(evaluation.get('overall_score', 0)) >= 4.0):
            evaluation['recommendation'] = 'maybe'

        logger.info(
            f"ASR floor applied: {substantive_turns} substantive turns detected, "
            f"scores floored at 4.0"
        )

    # Clamp scores to valid range
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
        'overall_score': 0.0,
        'technical_score': 0.0,
        'communication_score': 0.0,
        'cultural_fit_score': 0.0,
        'behavioral_score': 0.0,
        'strengths': [],
        'weaknesses': ['Evaluation could not be completed due to a system error'],
        'red_flags': ['⚠ AI evaluation failed — scores are not valid, manual review required'],
        'recommendation': 'manual_review',
        'interview_quality': 0,
        'technical_depth': 0,
        'behavioral_analysis': {
            'confidence_level': 'unknown',
            'engagement': 'unknown',
            'clarity': 'unknown'
        },
        'skill_assessment': {
            'relevant_skills_demonstrated': [],
            'missing_skills': []
        },
        'ai_feedback': {
            'summary': '⚠ AI evaluation failed. Please review the transcript manually.',
            'hiring_justification': 'System error occurred during evaluation. Manual review required.',
            'evaluation_error': True,
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