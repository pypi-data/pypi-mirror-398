from arabic_translator_tester.voice.mic import start_microphone
from arabic_translator_tester.voice.stt_vosk import ArabicSpeechRecognizer
from arabic_translator_tester.translator.argos import translate_arabic_to_english

def run_voice_translation(model_path: str):
    try:
        recognizer = ArabicSpeechRecognizer(model_path)
    except Exception as e:
        print(f"Error loading Vosk model: {e}")
        print(f"Make sure the model exists at: {model_path}")
        return
    
    try:
        stream, audio_queue = start_microphone()
    except Exception as e:
        print(f"Error starting microphone: {e}")
        print("Make sure your microphone is connected and accessible")
        return

    print("🎙 Speak Arabic (Ctrl+C to stop)")

    try:
        while True:
            audio = audio_queue.get()
            arabic = recognizer.accept_audio(audio)
            if arabic:
                print("Arabic:", arabic)
                try:
                    english = translate_arabic_to_english(arabic)
                    print("English:", english)
                except Exception as e:
                    print(f"Translation error: {e}")
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        stream.stop()
        print("Stopped.")