import sounddevice as sd
from scipy.io.wavfile import write
import subprocess
import tempfile
import os
import numpy as np

def find_MainFolder(icon_name):
    """Attempts to find the icon in and out of the script\'s directory."""  # inserted
    script_dir = os.path.dirname(os.path.realpath(__file__))
    possible_paths = [os.path.join(script_dir, icon_name), os.path.join(script_dir, 'Main', icon_name), os.path.abspath(os.path.join(script_dir, os.pardir, icon_name))]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    else:  # inserted
        return None

# -------------------- Configuration --------------------
EXE_PATH = find_MainFolder(r'Main/Engine/whisper-cli.exe')
MODEL_PATH = find_MainFolder(r'Main/Model/ggml-base.bin')
FS = 16000  # Sample rate in Hz
SILENCE_THRESHOLD = 500    # Energy threshold to detect silence
SILENCE_DURATION = 1.0     # Seconds of silence to stop recording
CHUNK_SLEEP_MS = 50        # Sleep between energy checks
MIN_SPEECH_DURATION = 0.2  # Minimum seconds of detected speech to transcribe
# -------------------------------------------------------

def record_until_silence():
    """Record from the microphone until silence is detected, then transcribe."""
    print("\nListening... Speak now.")

    recording = []
    silence_counter = 0
    speech_detected = False
    frames_recorded = 0

    def callback(indata, frames, time, status):
        nonlocal recording, silence_counter, speech_detected, frames_recorded
        if status:
            print(f"InputStream warning: {status}")
        recording.append(indata.copy())
        frames_recorded += frames

        energy = np.abs(indata).mean() * 32767
        if energy >= SILENCE_THRESHOLD:
            silence_counter = 0
            speech_detected = True
        else:
            silence_counter += frames / FS

    try:
        with sd.InputStream(channels=1, samplerate=FS, callback=callback):
            while silence_counter < SILENCE_DURATION:
                sd.sleep(CHUNK_SLEEP_MS)
    except Exception as e:
        print(f"Error accessing microphone: {e}")
        return

    # Skip if no meaningful speech was recorded
    if not speech_detected or frames_recorded / FS < MIN_SPEECH_DURATION:
        print("No speech detected, skipping transcription.")
        return

    audio = np.concatenate(recording, axis=0)
    audio_int16 = (audio * 32767).astype(np.int16)

    tmp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            write(tmp.name, FS, audio_int16)
            tmp_file = tmp.name

        # Transcribe
        result = subprocess.run(
            [EXE_PATH, "-m", MODEL_PATH, "-f", tmp_file],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            print("Transcription error:", result.stderr.strip())
        else:
            print("Recognized:", result.stdout.strip())

    except Exception as e:
        print(f"Error during transcription: {e}")
    finally:
        if tmp_file and os.path.exists(tmp_file):
            os.remove(tmp_file)


# -------------------- Main Loop --------------------
if __name__ == "__main__":
    print("Press Ctrl+C to stop.")
    while True:
        try:
            record_until_silence()
        except KeyboardInterrupt:
            print("\nStopped by user.")
            break
