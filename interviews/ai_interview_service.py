"""
AI Interview Service
Handles AI-powered interview conversations using DeepSeek via LangChain.
Loads conversation history from DB on every request so AI remembers context.

Requires: pip install langchain-openai
Env var:  DEEPSEEK_API_KEY=your-deepseek-api-key
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
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
    AI Interview Service using DeepSeek via LangChain ChatOpenAI.
    Reloads full conversation history from DB on each instantiation.
    """

    def __init__(self, interview_id: int):
        self.interview = Interview.objects.select_related(
            'job', 'candidate', 'candidate__user', 'agent'
        ).get(id=interview_id)

        # Initialize DeepSeek via LangChain (OpenAI-compatible)
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=config('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com",
            temperature=0.7,
            max_tokens=300,
        )

        # Get reference questions
        self.reference_questions = self._get_reference_questions()

        # Build system prompt
        self.system_prompt = self._build_system_prompt()

        # Initialize messages with system prompt
        self.messages: List = [
            SystemMessage(content=self.system_prompt)
        ]

        # Load previous conversation from DB
        history, q_count = self._load_history_from_db()
        self.messages.extend(history)
        self.questions_asked_count = q_count

    # ==========================================================
    # HISTORY LOADER
    # ==========================================================
    def _load_history_from_db(self):
        """
        Load all previous InterviewConversation rows and convert them
        into LangChain message format so the model remembers everything.
        """
        conversations = InterviewConversation.objects.filter(
            interview=self.interview
        ).order_by('timestamp')

        if not conversations.exists():
            return [], 0

        history = []
        ai_count = 0

        for conv in conversations:
            if conv.speaker == 'ai':
                # Avoid two consecutive AI entries
                if history and isinstance(history[-1], AIMessage):
                    history[-1].content += "\n" + conv.message
                else:
                    history.append(AIMessage(content=conv.message))
                ai_count += 1
            else:
                # Avoid two consecutive Human entries
                if history and isinstance(history[-1], HumanMessage):
                    history[-1].content += "\n" + conv.message
                else:
                    history.append(HumanMessage(content=conv.message))

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

4. **RESPONSE FORMAT & CONVERSATION FLOW:**
   - If answer is GOOD: Acknowledge in ONE sentence, then ask next question
   - If answer is VAGUE: Ask a follow-up for clarification
   - If answer is OFF-TOPIC: Gently redirect
   - Keep responses to 2-4 sentences MAX
   - ALWAYS end with a question for the candidate

5. **ENDING:**
   - After 5-7 questions, conclude naturally
   - Say: "Thank you so much for your time, [FirstName]! That concludes our interview. We'll review your responses and get back to you soon. Have a great day!"
   - Start message with "INTERVIEW_COMPLETE:"

**REMEMBER:**
- This is VOICE - be conversational
- Keep responses SHORT (2-4 sentences max)
- Ask ONE question at a time
- Be warm and encouraging
- NEVER repeat questions
- ALWAYS end with a question (except final message)
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
        self.messages.append(HumanMessage(content=message))

        response = self.llm.invoke(self.messages)
        text = response.content.strip()

        # Store assistant response in message history
        self.messages.append(AIMessage(content=text))

        # Trim to max 5 sentences for voice
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) > 5:
            text = '. '.join(sentences[:5]) + '.'

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