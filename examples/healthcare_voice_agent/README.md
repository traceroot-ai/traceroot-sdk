# Healthcare Voice Agent System

A multi-agent voice processing system designed for healthcare communication. This system converts patient voice queries to text, processes them with AI agents, and generates empathetic, informative voice responses with doctor recommendations.

## Features

- 🎤 Speech-to-Text conversion using OpenAI Whisper
- 🧠 Intelligent healthcare response planning
- 👩‍⚕️ Doctor recommendation and scheduling
- 💬 Natural language response generation
- 🔊 High-quality text-to-speech synthesis
- 📊 Visual workflow graph generation
- 🔍 **Full traceroot integration for monitoring and debugging**

## Architecture

The system follows a healthcare-focused workflow:

```
Input Audio → STT Agent → Healthcare Plan Agent → Doctor Search → Medical Response Agent → TTS Agent → Output Audio
```

## Traceroot Integration

This system is fully integrated with the traceroot monitoring system, providing:

- **Comprehensive logging**: All agent interactions and decisions are logged
- **Trace decorators**: Key methods are decorated with `@traceroot.trace()` for detailed monitoring
- **Error tracking**: Detailed error logging and debugging information
- **Performance monitoring**: Track execution times and bottlenecks
- **Agent interaction visibility**: See how data flows between agents

### Traced Components

All major components include traceroot integration:
- `VoiceAgentSystem.process_voice_query()`: Main workflow orchestration
- `VoiceAgentSystem.transcribe_node()`: Speech-to-text processing
- `VoiceAgentSystem.plan_node()`: Healthcare response planning
- `VoiceAgentSystem.doctor_search_node()`: Doctor recommendation search
- `VoiceAgentSystem.response_node()`: Medical response generation
- `VoiceAgentSystem.tts_node()`: Text-to-speech synthesis
- `VoicePlanAgent.plan_voice_response()`: Healthcare planning logic
- `VoiceResponseAgent.generate_response()`: Response generation
- `STTAgent.transcribe_audio()`: Audio transcription
- `TTSAgent.synthesize_speech()`: Speech synthesis
- `SchedulingAgent.find_available_doctors()`: Doctor search
- `SchedulingAgent.get_doctor_availability()`: Doctor availability

# Setup

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=your_api_key_here
```

# Run

```bash
cd ../../
python examples/healthcare_voice_agent/create_input_audio.py  # Generate test input
python examples/healthcare_voice_agent/main.py  # Run the system
```

## Testing Traceroot Integration

To test the traceroot integration without running the full voice pipeline:

```bash
cd ../../
python examples/healthcare_voice_agent/test_traceroot.py
```

This test script will:
- Verify trace decorators are working
- Test individual agents with traceroot logging
- Confirm all components are properly integrated
- Provide detailed logging output

## Components

- `main.py`: Core system orchestration with traceroot integration
- `stt_agent.py`: Speech-to-Text conversion with logging
- `plan_agent.py`: Healthcare response planning with tracing
- `scheduling_agent.py`: Doctor recommendations with monitoring
- `response_agent.py`: Medical response generation with tracing
- `tts_agent.py`: Text-to-Speech synthesis with logging
- `test_traceroot.py`: **Traceroot integration test script**
- `data/doctors.json`: Doctor database

## Example Input

The system comes with a sample healthcare query:
```
"Hi, I've been experiencing some concerning symptoms lately. For the past two weeks, 
I've been getting dizzy spells, especially when standing up quickly. I also notice 
I'm more tired than usual, and sometimes my heart feels like it's racing. I've been 
trying to stay hydrated, but I'm not sure if I should be worried about these symptoms. 
What should I do?"
```

## Output

The system generates:
1. A workflow visualization (`healthcare_voice_agent_graph.png`)
2. A voice response (`output_audio.wav`) containing:
   - Medical guidance
   - Doctor recommendations
   - Available appointment times
   - Next steps
3. **Comprehensive traceroot logs** showing:
   - Agent execution flow
   - Decision-making process
   - Performance metrics
   - Error details (if any)

## Dependencies

See `requirements.txt` for full list of dependencies:
- langchain & langgraph: Agent orchestration
- openai: GPT-4 for response generation
- whisper: Speech recognition
- coqui-tts: Text-to-speech synthesis
- **traceroot**: Monitoring and debugging system

## Important Notes

- This system is designed for general health information only
- Not a replacement for professional medical advice
- Always directs users to appropriate healthcare providers
- Maintains HIPAA compliance in all interactions
- Includes appropriate medical disclaimers
- **Full traceroot integration enables comprehensive monitoring and debugging** 