import json
from vosk import Model, KaldiRecognizer

class ArabicSpeechRecognizer:
    def __init__(self, model_path: str):
        try:
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
        except Exception as e:
            raise ValueError(f"Failed to load Vosk model from {model_path}: {e}")

    def accept_audio(self, audio: bytes) -> str | None:
        try:
            if self.recognizer.AcceptWaveform(audio):
                result = json.loads(self.recognizer.Result())
                return result.get("text")
        except Exception as e:
            print(f"Speech recognition error: {e}")
        return None