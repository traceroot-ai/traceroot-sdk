from typing import Any, Optional

import traceroot
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from traceroot.tracer import TraceOptions, trace

load_dotenv()

logger = traceroot.get_logger()


class VoicePlanResponse(BaseModel):
    """Structured response model for the healthcare voice planning agent"""
    plan: str = Field(description="Detailed plan for responding to the patient query")
    response_type: str = Field(description="Type of response needed: 'health_info', 'symptom_guidance', 'urgent_care_advisory', 'wellness_advice'")
    tone: str = Field(description="Suggested tone for the response: 'professional_caring', 'empathetic_informative', 'calm_reassuring'")


class VoicePlanAgent:
    """Agent for planning responses to healthcare voice queries"""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.3)
        self.system_prompt = (
            "You are a healthcare voice response planning agent. "
            "Your job is to analyze patient queries and create plans "
            "for generating appropriate healthcare responses. "
            "IMPORTANT GUIDELINES for healthcare planning: "
            "1. Assess query urgency and severity "
            "2. Include necessary medical disclaimers "
            "3. Plan responses that balance empathy with professionalism "
            "4. Structure information in easily digestible segments "
            "5. Include recommendations for professional medical care when appropriate "
            "6. Never plan to provide specific diagnoses "
            "7. Consider patient anxiety and emotional state "
            "8. Plan to explain medical terms in simple language "
            "9. Ensure HIPAA compliance in responses "
            "10. Include wellness and preventive advice when relevant "
            "Remember this will be spoken to a patient seeking health guidance."
        )
        self.plan_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt), 
            ("human", "Patient query transcript: {transcript}\n\nCreate a plan for responding to this healthcare query.")
        ])

    @trace(TraceOptions(trace_params=True, trace_return_value=True))
    def plan_voice_response(self, transcript: str) -> dict[str, Any]:
        """
        Analyze patient transcript and create response plan
        
        Args:
            transcript: The transcribed text from patient input
            
        Returns:
            Dict containing plan details for healthcare response generation
        """
        structured_llm = self.llm.with_structured_output(VoicePlanResponse)
        chain = self.plan_prompt | structured_llm

        formatted_prompt = self.plan_prompt.format(transcript=transcript)
        logger.info(f"HEALTHCARE PLAN AGENT prompt:\n{formatted_prompt}")

        response = chain.invoke({"transcript": transcript})

        logger.info(f"Healthcare planning for transcript: {transcript}")
        logger.info(f"Generated plan: {response.plan}")
        logger.info(f"Response type: {response.response_type}")
        logger.info(f"Suggested tone: {response.tone}")

        return {
            "transcript": transcript,
            "plan": response.plan,
            "response_type": response.response_type,
            "tone": response.tone
        }


def create_voice_plan_agent():
    return VoicePlanAgent() 