from TTS.api import TTS


def create_input_audio():
    """Create input audio file using Coqui TTS"""
    text = ("Hi, I've been experiencing some concerning symptoms lately. "
            "For the past two weeks, I've been getting dizzy spells, "
            "especially when standing up quickly. I also notice I'm more "
            "tired than usual, and sometimes my heart feels like it's racing. "
            "I've been trying to stay hydrated, but I'm not sure if I should "
            "be worried about these symptoms. What should I do?")

    # Initialize TTS with a good English model
    tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")

    # Save to file with full path
    output_path = "./examples/healthcare_voice_agent/input_audio.wav"
    tts.tts_to_file(text=text, file_path=output_path)
    print(f"✅ Created {output_path}")


if __name__ == "__main__":
    create_input_audio()
