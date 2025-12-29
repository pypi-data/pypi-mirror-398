import asyncio
import edge_tts
from pydub import AudioSegment
import simpleaudio as sa
import tempfile
import os

async def tts_to_play(text, voice="en-US-JennyNeural"):
    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    mp3_path = tmpfile.name
    tmpfile.close()

    try:
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(mp3_path)

        audio = AudioSegment.from_file(mp3_path, format="mp3")
        wav_bytes = audio.raw_data
        num_channels = audio.channels
        bytes_per_sample = audio.sample_width
        sample_rate = audio.frame_rate

        play_obj = sa.play_buffer(wav_bytes, num_channels, bytes_per_sample, sample_rate)
        play_obj.wait_done()

    finally:
        if os.path.exists(mp3_path):
            os.remove(mp3_path)

# Example usage with a different voice
text = """ """
voice = "en-CA-LiamNeural"  # <-- Change the voice here
asyncio.run(tts_to_play(text, voice))
