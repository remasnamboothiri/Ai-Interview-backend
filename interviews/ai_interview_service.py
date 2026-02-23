"""
AI Interview Service
Handles AI-powered interview conversations using Google Gemini directly (no LangChain)
Loads conversation history from DB on every request so AI remembers context.
"""

import google.generativeai as genai
from typing import Dict, List
from decouple import config
from .models import Interview
from job_custom_questions.models import JobCustomQuestion
from default_questions.models import DefaultQuestion
from candidate_documents.models import CandidateDocument
from interview_data.models import InterviewConversation
import logging

logger = logging.getLogger(__name__)


class AIInterviewService:
    """
    AI Interview Service for conducting voice-based conversational interviews.
    Reloads full conversation history from DB on each instantiation so the AI
    never loses context between HTTP requests.
    """

    def __init__(self, interview_id: int):
        self.interview = Interview.objects.select_related(
            'job', 'candidate', 'candidate__user', 'agent'
        ).get(id=interview_id)

        # Configure Gemini
        genai.configure(api_key=config('GEMINI_API_KEY'))

        # Get reference questions
        self.reference_questions = self._get_reference_questions()

        # Build system prompt
        self.system_prompt = self._build_system_prompt()

        # Initialize Gemini model with system instruction
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=self.system_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=150,
            )
        )

        # ── Load previous conversation from DB ───────────────
        history, q_count = self._load_history_from_db()
        self.chat = self.model.start_chat(history=history)
        self.questions_asked_count = q_count

    # ==========================================================
    # HISTORY LOADER — key fix for multi-request persistence
    # ==========================================================
    def _load_history_from_db(self):
        """
        Load all previous InterviewConversation rows and convert them
        into Gemini chat history format so the model remembers everything.
        
        Returns (history_list, questions_asked_count)
        """
        conversations = InterviewConversation.objects.filter(
            interview=self.interview
        ).order_by('timestamp')

        if not conversations.exists():
            return [], 0

        history = []
        ai_count = 0

        # Gemini requires the first message in history to be role="user".
        # The first DB entry is the AI greeting. We prepend the synthetic
        # intro prompt that originally triggered it.
        first = conversations.first()
        if first and first.speaker == 'ai':
            candidate_name = self.interview.candidate.user.full_name.split()[0]
            job_title = self.interview.job.title
            history.append({
                "role": "user",
                "parts": [
                    f"This is the START of the interview. "
                    f"Greet the candidate warmly using their first name ({candidate_name}) "
                    f"and the job title ({job_title}). Keep it SHORT and CONVERSATIONAL."
                ]
            })

        for conv in conversations:
            if conv.speaker == 'ai':
                # Avoid two consecutive "model" entries
                if history and history[-1]["role"] == "model":
                    # Merge with previous model message
                    history[-1]["parts"][0] += "\n" + conv.message
                else:
                    history.append({"role": "model", "parts": [conv.message]})
                ai_count += 1
            else:
                # Avoid two consecutive "user" entries
                if history and history[-1]["role"] == "user":
                    history[-1]["parts"][0] += "\n" + conv.message
                else:
                    history.append({"role": "user", "parts": [conv.message]})

        logger.info(
            f"Loaded {len(conversations)} messages for interview {self.interview.id} "
            f"({ai_count} AI messages)"
        )

        return history, ai_count

    # ==========================================================
    # SYSTEM PROMPT
    # ==========================================================
    def _build_system_prompt(self) -> str:
        job = self.interview.job
        agent = self.interview.agent
        candidate = self.interview.candidate
        resume_content = self._get_candidate_resume()

        reference_questions_text = "\n".join([
            f"{i+1}. {q}" for i, q in enumerate(self.reference_questions)
        ]) if self.reference_questions else "No specific questions - use your judgment."

        return f"""You are a professional AI interviewer conducting a VOICE-BASED interview.

**CRITICAL: This is a VOICE interview - Keep ALL responses SHORT and CONVERSATIONAL**

**Your Personality:**
{agent.system_prompt if agent else "Professional, warm, and encouraging"}

**Interview Type:** {agent.interview_type if agent else "technical and behavioral"}

**Job Details:**
- Position: {job.title}
- Experience Level: {job.experience_level}
- Skills Required: {', '.join(job.skills_required) if job.skills_required else 'Not specified'}

**Candidate:**
- Name: {candidate.user.full_name}
- Experience: {candidate.experience_years} years
- Current Company: {candidate.current_company or 'Not specified'}

**Resume:**
{resume_content}

**REFERENCE QUESTIONS (guidance only):**
{reference_questions_text}

**VOICE INTERVIEW RULES:**

1. **GREETING (First message only):**
   - Greet warmly: "Hello [FirstName]! Welcome to your interview for [Position]. I'm your AI interviewer today. How are you doing?"

2. **ICE-BREAKER (Second message):**
   - After greeting response, ask: "Great! Let's begin. Tell me a bit about yourself and your background."

3. **MAIN QUESTIONS:**
   - Use reference questions as guidance
   - Ask ONE question at a time
   - Keep questions clear and concise
   - Ask 5-7 questions total
   - NEVER repeat a question you already asked
   - Keep track of how many questions you've asked

4. **RESPONSE FORMAT:**
   - Maximum 2-3 sentences
   - Acknowledge briefly: "I see" or "Thank you"
   - Then ask next question
   - NO long explanations

5. **ENDING:**
   - After 5-7 questions, conclude naturally
   - Say: "Thank you so much for your time, [FirstName]! That concludes our interview. We'll review your responses and get back to you soon. Have a great day!"
   - Start message with "INTERVIEW_COMPLETE:"

**REMEMBER:**
- This is VOICE - be conversational
- Keep responses SHORT (2-3 sentences max)
- Ask ONE question at a time
- Be warm and encouraging
- NEVER repeat questions you already asked
"""

    def _get_candidate_resume(self) -> str:
        try:
            resume_doc = CandidateDocument.objects.filter(
                candidate=self.interview.candidate,
                is_primary=True
            ).first()
            return f"Resume: {resume_doc.file_name}" if resume_doc else "No resume uploaded"
        except Exception:
            return "Resume not available"

    def _get_reference_questions(self) -> List[str]:
        questions = []
        for jq in JobCustomQuestion.objects.filter(job=self.interview.job).order_by('id'):
            questions.append(jq.question_text)
        if self.interview.agent:
            for aq in DefaultQuestion.objects.filter(agent=self.interview.agent).order_by('id'):
                questions.append(aq.question_text)
        if not questions:
            questions = [
                "Tell me about yourself and your professional background.",
                "What interests you about this position?",
                "Can you describe a challenging project you've worked on?",
                "What are your key strengths for this role?",
                "Where do you see yourself in the next few years?"
            ]
        return questions

    # ==========================================================
    # CHAT
    # ==========================================================
    def _chat_send(self, message: str) -> str:
        response = self.chat.send_message(message)
        text = response.text
        # Trim to first 2 sentences max for speed
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) > 3:
            text = '. '.join(sentences[:3]) + '.'
        return text

    def start_interview(self) -> Dict:
        candidate_first_name = self.interview.candidate.user.full_name.split()[0]
        job_title = self.interview.job.title

        ai_response = self._chat_send(
            f"This is the START of the interview. "
            f"Greet the candidate warmly using their first name ({candidate_first_name}) "
            f"and the job title ({job_title}). "
            f"Keep it SHORT and CONVERSATIONAL (2-3 sentences max)."
        )

        self.questions_asked_count += 1

        return {
            "status": "started",
            "message": ai_response,
            "current_question": ai_response,
            "question_number": self.questions_asked_count,
            "total_questions": len(self.reference_questions) + 2,
            "is_complete": False
        }

    def send_message(self, candidate_message: str) -> Dict:
        ai_response = self._chat_send(candidate_message)

        self.questions_asked_count += 1

        is_complete = "INTERVIEW_COMPLETE:" in ai_response

        if is_complete:
            ai_response = ai_response.replace("INTERVIEW_COMPLETE:", "").strip()

        return {
            "status": "in_progress",
            "message": ai_response,
            "current_question": ai_response,
            "question_number": self.questions_asked_count,
            "total_questions": len(self.reference_questions) + 2,
            "is_complete": is_complete
        }

    def end_interview(self) -> Dict:
        return {
            "status": "completed",
            "message": "Interview completed successfully. Thank you for your time!",
            "total_questions_asked": self.questions_asked_count
        }


