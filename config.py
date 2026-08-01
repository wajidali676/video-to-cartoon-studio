"""
All settings — fully adjustable for Kaggle P100 (16GB VRAM)
Memory-optimized for 1-minute videos
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "outputs")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# VRAM & Memory Management
MAX_VRAM_GB = 14          # Leave 2GB buffer
BATCH_SIZE = 1            # Process 1 frame at a time (safest for P100)
CLEAR_CACHE_EVERY = 3     # Clear VRAM every N segments

# Video Limits
MAX_VIDEO_DURATION = 60   # 1 minute max
DEFAULT_SEGMENT_DURATION = 5
TARGET_FPS = 30

# Edge-TTS Voices (High Quality, Free, No model download)
VOICE_MAP = {
    "en": "en-US-AriaNeural",
    "ur": "ur-PK-AsadNeural",
    "hi": "hi-IN-MadhurNeural",
    "ar": "ar-SA-HamedNeural",
    "es": "es-ES-ElviraNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural"
}

LANG_NAMES = {
    "en": "English", "ur": "Urdu", "hi": "Hindi", "ar": "Arabic",
    "es": "Spanish", "fr": "French", "de": "German", "zh": "Chinese",
    "ja": "Japanese", "ko": "Korean"
}
