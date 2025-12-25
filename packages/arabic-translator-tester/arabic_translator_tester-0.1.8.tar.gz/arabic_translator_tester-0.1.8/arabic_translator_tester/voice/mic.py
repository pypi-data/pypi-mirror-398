import sounddevice as sd
import queue

def _callback(indata, frames, time, status):
    # Access the queue from the closure
    _callback.audio_queue.put(bytes(indata))

def start_microphone():
    audio_queue = queue.Queue()
    _callback.audio_queue = audio_queue  # Attach queue to callback
    
    stream = sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=_callback,
    )
    stream.start()
    return stream, audio_queue