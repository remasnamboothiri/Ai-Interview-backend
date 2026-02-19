"""
AI Interview Service
Handles AI-powered interview conversations using Google Gemini
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Dict, List
from decouple import config
from .models import Interview
from job_custom_questions.models import JobCustomQuestion
from default_questions.models import DefaultQuestion
from candidate_documents.models import CandidateDocument
import logging

logger = logging.getLogger(__name__)


class AIInterviewService:
    """
    AI Interview Service for conducting voice-based conversational interviews
    """
    
    def __init__(self, interview_id: int):
        """Initialize AI Interview Service"""
        self.interview = Interview.objects.select_related(
            'job', 'candidate', 'candidate__user', 'agent'
        ).get(id=interview_id)
        
        # Get Gemini API key
        gemini_api_key = config('GEMINI_API_KEY')
        
        # Initialize Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=gemini_api_key,
            temperature=0.7,
            max_tokens=300  # Keep responses concise for voice
        )
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Get reference questions
        self.reference_questions = self._get_reference_questions()
        
        # Build system prompt
        self.system_prompt = self._build_system_prompt()
        
        # Track questions
        self.questions_asked_count = 0
        
    def _build_system_prompt(self) -> str:
        """Build system prompt for voice-based interview"""
        job = self.interview.job
        agent = self.interview.agent
        candidate = self.interview.candidate
        
        # Get candidate resume
        resume_content = self._get_candidate_resume()
        
        # Format reference questions
        reference_questions_text = "\n".join([
            f"{i+1}. {q}" for i, q in enumerate(self.reference_questions)
        ]) if self.reference_questions else "No specific questions - use your judgment."
        
        prompt = f"""You are a professional AI interviewer conducting a VOICE-BASED interview.

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

4. **RESPONSE FORMAT:**
   - Maximum 2-3 sentences
   - Acknowledge briefly: "I see" or "Thank you"
   - Then ask next question
   - NO long explanations

5. **ENDING:**
   - After 5-7 questions, conclude naturally
   - Say: "Thank you so much for your time, [FirstName]! That concludes our interview. We'll review your responses and get back to you soon. Have a great day!"
   - Start message with "INTERVIEW_COMPLETE:"

**EXAMPLE FLOW:**
AI: "Hello John! Welcome to your interview for Software Engineer. I'm your AI interviewer today. How are you doing?"
Candidate: "I'm doing well, thank you!"
AI: "Great! Let's begin. Tell me a bit about yourself and your background."
Candidate: [answers]
AI: "Thank you for sharing. Now, can you describe your experience with Python?"
...
AI: "INTERVIEW_COMPLETE: Thank you so much for your time, John! That concludes our interview. We'll review your responses and get back to you soon. Have a great day!"

**REMEMBER:**
- This is VOICE - be conversational
- Keep responses SHORT (2-3 sentences max)
- Ask ONE question at a time
- Be warm and encouraging
"""
        return prompt
    
    def _get_candidate_resume(self) -> str:
        """Get candidate's resume content"""
        try:
            resume_doc = CandidateDocument.objects.filter(
                candidate=self.interview.candidate,
                is_primary=True
            ).first()
            
            if resume_doc:
                return f"Resume: {resume_doc.file_name}"
            else:
                return "No resume uploaded"
        except Exception as e:
            return "Resume not available"
    
    def _get_reference_questions(self) -> List[str]:
        """Get reference questions for guidance"""
        questions = []
        
        # Get custom questions from job
        job_questions = JobCustomQuestion.objects.filter(
            job=self.interview.job
        ).order_by('id')
        
        for jq in job_questions:
            questions.append(jq.question_text)
        
        # Get default questions from agent
        if self.interview.agent:
            agent_questions = DefaultQuestion.objects.filter(
                agent=self.interview.agent
            ).order_by('id')
            
            for aq in agent_questions:
                questions.append(aq.question_text)
        
        # Fallback questions
        if not questions:
            questions = [
                "Tell me about yourself and your professional background.",
                "What interests you about this position?",
                "Can you describe a challenging project you've worked on?",
                "What are your key strengths for this role?",
                "Where do you see yourself in the next few years?"
            ]
        
        return questions
    
    def start_interview(self) -> Dict:
        """Start the interview with greeting"""
        # Create conversation chain
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        self.conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=prompt_template,
            verbose=False
        )
        
        # Get AI's greeting
        candidate_first_name = self.interview.candidate.user.full_name.split()[0]
        job_title = self.interview.job.title
        
        intro_prompt = f"""This is the START of the interview. 

Greet the candidate warmly using their first name ({candidate_first_name}) and the job title ({job_title}).

Follow the GREETING format from your instructions.

Keep it SHORT and CONVERSATIONAL (2-3 sentences max)."""
        
        ai_response = self.conversation.predict(input=intro_prompt)
        
        self.questions_asked_count += 1
        
        return {
            "status": "started",
            "message": ai_response,
            "current_question": ai_response,
            "question_number": self.questions_asked_count,
            "total_questions": len(self.reference_questions) + 2,  # +2 for greeting and ice-breaker
            "is_complete": False
        }
    
    def send_message(self, candidate_message: str) -> Dict:
        """Process candidate's answer and get AI's response"""
        # Initialize conversation if not exists
        if not hasattr(self, 'conversation') or self.conversation is None:
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}")
            ])
            
            self.conversation = ConversationChain(
                llm=self.llm,
                memory=self.memory,
                prompt=prompt_template,
                verbose=False
            )
        
        # Get AI response
        ai_response = self.conversation.predict(input=candidate_message)
        
        self.questions_asked_count += 1
        
        # Check if interview is complete
        is_complete = "INTERVIEW_COMPLETE:" in ai_response
        
        # Remove the marker from response if present
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
        """End the interview and return summary"""
        return {
            "status": "completed",
            "message": "Interview completed successfully. Thank you for your time!",
            "total_questions_asked": self.questions_asked_count
        }
