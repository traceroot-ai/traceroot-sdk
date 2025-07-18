import os
from typing import Any, Dict, List, Optional, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from plan_agent import create_voice_plan_agent
from response_agent import create_voice_response_agent
from scheduling_agent import create_scheduling_agent
from stt_agent import create_stt_agent
from tts_agent import create_tts_agent

import traceroot
from traceroot.tracer import TraceOptions, trace

load_dotenv()

logger = traceroot.get_logger()


class VoiceAgentState(TypedDict):
    """State object for the voice agent workflow"""
    transcript: Optional[str]
    plan: Optional[Dict[str, Any]]
    response: Optional[str]
    doctor_recommendations: Optional[List[Dict[str, Any]]]
    selected_doctor: Optional[Dict[str, Any]]
    output_path: Optional[str]
    error: Optional[str]
    input_path: Optional[str]


class VoiceAgentSystem:
    r"""Enhanced healthcare voice agent system with scheduling
    capabilities"""

    def __init__(self):
        r"""Enhanced healthcare voice agent system with
        scheduling capabilities
        """
        logger.info("🔧 Initializing Voice Agent System...")
        self.stt_agent = create_stt_agent()
        logger.info("✅ STT Agent initialized")
        self.plan_agent = create_voice_plan_agent()
        logger.info("✅ Planning Agent initialized")
        self.response_agent = create_voice_response_agent()
        logger.info("✅ Response Agent initialized")
        self.scheduling_agent = create_scheduling_agent()
        logger.info("✅ Scheduling Agent initialized")
        self.tts_agent = create_tts_agent()
        logger.info("✅ TTS Agent initialized")
        self.graph = self._build_graph()
        logger.info("✅ Workflow graph compiled successfully")

    def _build_graph(self):
        """Build the enhanced voice processing workflow graph"""
        workflow = StateGraph(VoiceAgentState)

        # Add nodes with simple Mermaid-compatible names
        # (no spaces, no special chars)
        workflow.add_node("SpeechToText", self.transcribe_node)
        workflow.add_node("Planning", self.plan_node)
        workflow.add_node("DoctorSearch", self.doctor_search_node)
        workflow.add_node("Response", self.response_node)
        workflow.add_node("TextToSpeech", self.tts_node)
        workflow.add_node("Final", self.final_node)

        # Add edges with simplified names
        workflow.set_entry_point("SpeechToText")
        workflow.add_conditional_edges("SpeechToText",
                                       self.should_continue_after_stt, {
                                           "continue": "Planning",
                                           "end": "Final"
                                       })
        workflow.add_edge("Planning", "DoctorSearch")
        workflow.add_edge("DoctorSearch", "Response")
        workflow.add_edge("Response", "TextToSpeech")
        workflow.add_edge("TextToSpeech", "Final")
        workflow.add_edge("Final", END)

        return workflow.compile()

    @trace(TraceOptions(trace_params=True, trace_return_value=True))
    def transcribe_node(self, state: VoiceAgentState) -> Dict[str, Any]:
        """Process audio input to text"""
        logger.info("\n🎤 Starting Speech-to-Text processing...")
        try:
            result = self.stt_agent.transcribe_audio(state["input_path"])
            transcript = result["transcript"]
            logger.info("✅ STT completed successfully")
            logger.info(f"📝 Transcript: {transcript}")
            return {"transcript": transcript}
        except Exception as e:
            logger.error(f"❌ STT failed: {str(e)}")
            return {"error": f"STT failed: {str(e)}"}

    @trace(TraceOptions(trace_params=True, trace_return_value=True))
    def plan_node(self, state: VoiceAgentState) -> Dict[str, Any]:
        """Create healthcare response plan"""
        logger.info("\n🧠 Starting response planning...")
        try:
            plan = self.plan_agent.plan_voice_response(state["transcript"])
            logger.info("✅ Planning completed successfully")
            logger.info(f"📋 Plan: {plan}")
            return {"plan": plan}
        except Exception as e:
            logger.error(f"❌ Planning failed: {str(e)}")
            return {"error": f"Planning failed: {str(e)}"}

    @trace(TraceOptions(trace_params=True, trace_return_value=True))
    def doctor_search_node(self, state: VoiceAgentState) -> Dict[str, Any]:
        """Search for appropriate doctors based on patient needs"""
        logger.info("\n👨‍⚕️ Starting doctor search...")
        try:
            # Extract symptoms and preferences from transcript
            symptoms = self._extract_symptoms(state["transcript"])
            specialty = self._determine_specialty(symptoms, state["plan"])

            logger.info(f"🔍 Extracted symptoms: {symptoms}")
            logger.info(f"🏥 Determined specialty: {specialty}")

            # Find available doctors
            recommendations = self.scheduling_agent.find_available_doctors(
                specialty=specialty, symptoms=symptoms)

            # Fix Pydantic deprecation warning
            doctor_recs = [rec.model_dump() for rec in recommendations[:3]]

            logger.info(f"✅ Found {len(doctor_recs)} doctor recommendations")
            for i, doc in enumerate(doctor_recs, 1):
                logger.info(f"   {i}. {doc['name']} - {doc['specialty']}")

            return {"doctor_recommendations": doctor_recs}
        except Exception as e:
            logger.error(f"❌ Doctor search failed: {str(e)}")
            return {"error": f"Doctor search failed: {str(e)}"}

    @trace(TraceOptions(trace_params=True, trace_return_value=True))
    def response_node(self, state: VoiceAgentState) -> Dict[str, Any]:
        """Generate enhanced response with doctor recommendations"""
        logger.info("\n💬 Starting response generation...")
        try:
            response = self.response_agent.generate_response(
                transcript=state["transcript"],
                plan=state["plan"]["plan"],
                response_type=state["plan"]["response_type"],
                tone=state["plan"]["tone"],
                doctor_recommendations=state["doctor_recommendations"])
            logger.info("✅ Response generated successfully")
            logger.info(f"📄 Response preview: {response[:200]}...")
            return {"response": response}
        except Exception as e:
            logger.error(f"❌ Response generation failed: {str(e)}")
            return {"error": f"Response generation failed: {str(e)}"}

    @trace(TraceOptions(trace_params=True, trace_return_value=True))
    def tts_node(self, state: VoiceAgentState) -> Dict[str, Any]:
        """Convert response to speech"""
        logger.info("\n🔊 Starting Text-to-Speech synthesis...")
        try:
            # Save in the healthcare_voice_agent directory
            output_path = "./examples/healthcare_voice_agent/output_audio.wav"
            logger.info(f"🎵 Attempting to save audio to: {output_path}")
            logger.info(f"📝 Text to synthesize: {state['response'][:100]}...")

            # Call TTS agent and get detailed response
            result = self.tts_agent.synthesize_speech(state["response"],
                                                      output_path)

            # Check the TTS agent's response
            if result and result.get("success"):
                logger.info("✅ TTS agent reported success")
            else:
                logger.error(f"⚠️  TTS agent reported failure: "
                             f"{result.get('error', 'Unknown error')}")

            # Verify the file was created
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info("✅ TTS completed successfully")
                logger.info(f"🎵 Audio saved to: {output_path}")
                logger.info(f"📁 File size: {file_size} bytes")
            else:
                logger.warning(f"⚠️  File was not created at "
                               f"expected location: {output_path}")
                logger.info(f"🔍 Current working directory: {os.getcwd()}")
                # Check if file was created in current directory
                if os.path.exists("output_audio.wav"):
                    logger.info(
                        f"📁 File found in current directory "
                        f"instead: {os.path.abspath('output_audio.wav')}")

            return {"output_path": output_path}
        except Exception as e:
            logger.error(f"❌ TTS failed: {str(e)}")
            logger.info(f"🔍 Current working directory: {os.getcwd()}")
            return {"error": f"TTS failed: {str(e)}"}

    def final_node(self, state: VoiceAgentState) -> Dict[str, Any]:
        """Final node that handles both success and error cases"""
        logger.info("\n🏁 Workflow completed!")
        return {}

    def should_continue_after_stt(self, state: VoiceAgentState) -> str:
        """Determine if processing should continue after STT"""
        if state.get("error"):
            logger.warning("⚠️  STT error detected, ending workflow")
            return "end"
        logger.info("✅ STT successful, continuing to planning")
        return "continue"

    def _extract_symptoms(self, transcript: str) -> List[str]:
        """Extract symptoms from patient transcript"""
        # This would use NLP to extract symptoms
        # For now, using a simple keyword-based approach
        common_symptoms = [
            "headache", "pain", "fever", "cough", "fatigue", "dizziness",
            "nausea", "anxiety", "depression"
        ]
        return [s for s in common_symptoms if s in transcript.lower()]

    def _determine_specialty(self, symptoms: List[str],
                             plan: Dict[str, Any]) -> Optional[str]:
        """Determine appropriate medical specialty based on symptoms"""
        # This would use more sophisticated logic
        # For now, using simple mapping
        specialty_mapping = {
            "headache": "Neurology",
            "anxiety": "Psychiatry",
            "depression": "Psychiatry",
            "pain": "Pain Management",
            "fever": "Internal Medicine",
            "cough": "Pulmonology"
        }

        for symptom in symptoms:
            if symptom in specialty_mapping:
                return specialty_mapping[symptom]

        return None

    @trace(TraceOptions(trace_params=True, trace_return_value=True))
    def process_voice_query(self, input_path: str) -> str:
        """Process voice query and return path to response audio"""
        logger.info(f"Processing voice query from: {input_path}")
        initial_state = {
            "transcript": None,
            "plan": None,
            "response": None,
            "doctor_recommendations": None,
            "selected_doctor": None,
            "output_path": None,
            "error": None,
            "input_path": input_path
        }

        result = self.graph.invoke(initial_state)

        if result.get("error"):
            logger.error(f"Voice query processing failed: {result['error']}")
            raise Exception(result["error"])

        logger.info(f"Voice query processed successfully, "
                    f"output: {result.get('output_path')}")
        return result.get("output_path")

    def draw_and_save_graph(
        self,
        output_path: str = "./examples/healthcare_voice_agent/graph.png",
    ) -> None:
        """Draw the voice agent workflow graph and save it locally"""
        try:
            # Try to render the PNG
            mermaid_png = self.graph.get_graph().draw_mermaid_png()
            # if the above fails, try this:
            # from langchain_core.runnables.graph import MermaidDrawMethod
            # mermaid_png = self.graph.get_graph().draw_mermaid_png(
            #   draw_method=MermaidDrawMethod.PYPPETEER)
            with open(output_path, "wb") as f:
                f.write(mermaid_png)
            logger.info(f"✅ Workflow graph saved as PNG to: {output_path}")

        except Exception as e:
            logger.error(f"❌ Could not save workflow graph: {str(e)}")
            logger.info("This is likely due to network "
                        "connectivity issues with the Mermaid API.")
            logger.info("The voice agent will still work "
                        "normally without the graph visualization.")


def main():
    """Main function to demonstrate the voice agent system"""
    logger.info("🚀 Starting Healthcare Voice Agent Demo")
    logger.info("=" * 50)

    if not os.getenv("OPENAI_API_KEY"):
        logger.error("❌ Please set your OPENAI_API_KEY environment variable")
        logger.info("You can create a .env file with: "
                    "OPENAI_API_KEY=your_api_key_here")
        return

    system = VoiceAgentSystem()

    logger.info("\n📊 Attempting to save workflow graph...")
    # Save the workflow graph
    system.draw_and_save_graph()

    # Example usage
    example_audio = "./examples/healthcare_voice_agent/input_audio.wav"

    if os.path.exists(example_audio):
        logger.info(f"\n🎯 Processing audio file: {example_audio}")
        logger.info("=" * 50)
        try:
            output_path = system.process_voice_query(example_audio)
            logger.info("\n" + "=" * 50)
            logger.info(f"🎉 SUCCESS! Response audio saved to: {output_path}")
            logger.info("=" * 50)
        except Exception as e:
            logger.error(f"\n❌ Processing failed: {str(e)}")
    else:
        logger.warning(f"\n📁 No audio file found at: {example_audio}")
        logger.info("Please run create_input_audio.py first "
                    "to generate the input audio file")


if __name__ == "__main__":
    main()
