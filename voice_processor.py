"""
Voice Processing: Extract, Pitch Shift, TTS
Uses Edge-TTS (free, high quality, no model download)
Uses faster-whisper for STT
"""
import os
import subprocess
import asyncio
import edge_tts
from pydub import AudioSegment
from config import VOICE_MAP

class VoiceProcessor:
    def __init__(self, model_manager=None):
        self.model_manager = model_manager

    def extract_text(self, audio_path):
        if self.model_manager is None:
            return ""
        model = self.model_manager.load_whisper_model()
        if model is None:
            return ""
        segments, _ = model.transcribe(audio_path, language=None)
        text = " ".join([seg.text for seg in segments])
        return text.strip()

    def change_pitch(self, audio_path, output_path, semitones=0):
        if semitones == 0:
            audio = AudioSegment.from_file(audio_path)
            audio.export(output_path, format="wav")
            return output_path

        cmd = [
            "ffmpeg", "-y", "-i", audio_path,
            "-af", f"asetrate=44100*2^({semitones}/12),aresample=44100",
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return output_path

    async def text_to_speech(self, text, output_path, language="en"):
        voice = VOICE_MAP.get(language, "en-US-AriaNeural")
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return output_path

    def text_to_speech_sync(self, text, output_path, language="en"):
        return asyncio.run(self.text_to_speech(text, output_path, language))
