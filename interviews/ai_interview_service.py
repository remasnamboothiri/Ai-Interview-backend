from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Dict, List
from decouple import config  #  To read from .env file
from .models import Interview
from job_custom_questions.models import JobCustomQuestion
from default_questions.models import DefaultQuestion
from candidate_documents.models import CandidateDocument


class AIInterviewService:
    """
    AI Interview Service for conducting dynamic, conversational interviews
    using Google's Gemini 2.5 Flash model.
    
    This service conducts INTELLIGENT interviews where:
    - AI generates questions dynamically based on conversation
    - AI asks follow-up questions based on candidate's answers
    - Default questions serve as REFERENCE/GUIDANCE, not mandatory script
    - AI decides when interview is complete based on information gathered
    """
    
    def __init__(self, interview_id: int):
        """
        Initialize AI Interview Service
        
        Args:
            interview_id: ID of the interview to conduct
        """
        # Get interview object
        self.interview = Interview.objects.select_related(
            'job', 'candidate', 'candidate__user', 'agent'
        ).get(id=interview_id)
        
        # Get Gemini API key from .env file
        gemini_api_key = config('GEMINI_API_KEY')
        
        # Initialize Gemini 2.5 Flash model
        # Note: The parameter name is 'google_api_key' (library requirement)
        # but we're using GEMINI_API_KEY from our .env file
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=gemini_api_key,  # ← Using Gemini API key here
            temperature=0.7,
            max_tokens=500
        )
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Get reference questions (for AI guidance only)
        self.reference_questions = self._get_reference_questions()
        # Build the system prompt
        self.system_prompt = self._build_system_prompt()
        
        
        
        
        # Track questions asked (for analytics)
        self.questions_asked_count = 0
        
    def _build_system_prompt(self) -> str:
        """
        Build system prompt for DYNAMIC interview
        """
        job = self.interview.job
        agent = self.interview.agent
        candidate = self.interview.candidate
        
        # Get candidate resume
        resume_content = self._get_candidate_resume()
        
        # Format reference questions
        reference_questions_text = "\n".join([
            f"{i+1}. {q}" for i, q in enumerate(self.reference_questions)
        ]) if self.reference_questions else "No specific questions provided - use your judgment."
        
        # Build dynamic interview prompt
        prompt = f"""You are an AI interviewer conducting a DYNAMIC, CONVERSATIONAL job interview.

**Your Role and Personality:**
{agent.system_prompt if agent else "You are a professional, friendly, and insightful interviewer."}

**Interview Type:** {agent.interview_type if agent else "technical and behavioral"}

**Job Details:**
- Position: {job.title}
- Experience Level: {job.experience_level}
- Skills Required: {', '.join(job.skills_required) if job.skills_required else 'Not specified'}
- Employment Type: {job.employment_type}
- Work Mode: {job.work_mode}

**Job Description:**
{job.description}

**Job Requirements:**
{job.requirements}

**Candidate Information:**
- Name: {candidate.user.full_name}
- Experience: {candidate.experience_years} years
- Current Company: {candidate.current_company or 'Not specified'}
- Skills: {', '.join(candidate.skills) if candidate.skills else 'Not specified'}

**Candidate Resume:**
{resume_content}

**REFERENCE QUESTIONS (Use as guidance, not mandatory script):**
{reference_questions_text}

**INTERVIEW INSTRUCTIONS:**

1. **DYNAMIC QUESTIONING:**
   - Use reference questions as GUIDANCE only
   - Ask follow-up questions based on candidate's answers
   - Explore topics deeper based on responses
   - Adapt questions to candidate's experience level

2. **CONVERSATIONAL FLOW:**
   - Listen carefully to answers
   - Ask clarifying questions when needed
   - Connect questions to previous answers
   - Make interview feel natural, not scripted

3. **RESPONSE FORMAT:**
   - Keep responses concise (2-3 sentences max)
   - Acknowledge answer briefly
   - Then ask your next question
   - Be professional but warm

4. **INTERVIEW COMPLETION:**
   - Conduct approximately 5-10 questions
   - When you have sufficient information, conclude naturally
   - To end: Start message with "INTERVIEW_COMPLETE:" followed by closing

**IMPORTANT RULES:**
- Ask ONE question at a time
- Be encouraging and professional
- When ready to end, start message with "INTERVIEW_COMPLETE:"
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
                return f"Resume: {resume_doc.file_name}\nURL: {resume_doc.document_url}"
            else:
                return "No resume uploaded"
        except Exception as e:
            return f"Resume not available: {str(e)}"
    
    def _get_reference_questions(self) -> List[str]:
        """
        Get reference questions for AI GUIDANCE (not mandatory)
        """
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
        
        # Fallback questions if none found
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
        """
        Start the interview with AI-generated opening
        """
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
        
        # Let AI start the interview naturally
        intro_prompt = """Start the interview now. 

Greet the candidate warmly, briefly introduce yourself, and ask your first question.

Consider the candidate's experience level, job requirements, and reference questions provided.

Keep your response concise and professional."""
        
        ai_response = self.conversation.predict(input=intro_prompt)
        
        # Increment questions counter
        self.questions_asked_count += 1
        
        return {
            "status": "started",
            "message": ai_response,
            "question_number": self.questions_asked_count,
            "total_questions": len(self.reference_questions),
            "current_question": "Dynamic - AI generated"
        }
    
    def send_message(self, candidate_message: str) -> Dict:
        """
        Process candidate's answer and get AI's dynamic response
        """
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
        
        # Let AI continue the conversation naturally
        continue_prompt = f"""The candidate answered: "{candidate_message}"

Now continue the interview:

1. Briefly acknowledge their answer (1 sentence)
2. Then either:
   - Ask a relevant follow-up question to explore deeper, OR
   - Move to a new topic from the reference questions, OR
   - If you have gathered sufficient information (typically after 5-10 questions), conclude the interview

If concluding, start your response with "INTERVIEW_COMPLETE:" followed by your closing message.

Otherwise, ask your next question naturally."""
        
        ai_response = self.conversation.predict(input=continue_prompt)
        
        # Increment questions counter
        self.questions_asked_count += 1
        
        # Check if AI decided to complete the interview
        is_complete = ai_response.strip().startswith("INTERVIEW_COMPLETE:")
        
        if is_complete:
            # Remove the completion marker from the message
            ai_response = ai_response.replace("INTERVIEW_COMPLETE:", "").strip()
            
            return {
                "status": "completed",
                "message": ai_response,
                "question_number": self.questions_asked_count,
                "total_questions": len(self.reference_questions),
                "is_complete": True
            }
        else:
            # Interview continues
            return {
                "status": "in_progress",
                "message": ai_response,
                "question_number": self.questions_asked_count,
                "total_questions": len(self.reference_questions),
                "current_question": "Dynamic - AI generated",
                "is_complete": False
            }
    
    def get_conversation_history(self) -> List[Dict]:
        """Get full conversation history"""
        messages = []
        for message in self.memory.chat_memory.messages:
            messages.append({
                "role": "ai" if message.type == "ai" else "human",
                "content": message.content
            })
        return messages
    
    def end_interview(self) -> Dict:
        """End the interview and return summary"""
        conversation_history = self.get_conversation_history()
        
        return {
            "status": "ended",
            "total_questions_asked": self.questions_asked_count,
            "conversation_length": len(conversation_history),
            "message": "Interview completed successfully"
        }
