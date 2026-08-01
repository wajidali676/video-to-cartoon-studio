"""
GPU VRAM management — lazy load models, clear cache between segments
Optimized for Kaggle P100 16GB
"""
import torch
import gc

class ModelManager:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.anime_model = None
        self.whisper_model = None
        print(f"[ModelManager] Device: {self.device}")

    def load_anime_model(self):
        if self.anime_model is None:
            try:
                print("[ModelManager] Loading AnimeGAN2...")
                self.anime_model = torch.hub.load(
                    "bryandlee/animegan2-pytorch:main",
                    "generator",
                    pretrained=True,
                    device=self.device
                )
                self.anime_model.eval()
                print("[ModelManager] ✓ AnimeGAN2 ready")
            except Exception as e:
                print(f"[ModelManager] ✗ AnimeGAN2 failed: {e}")
                self.anime_model = None
        return self.anime_model

    def load_whisper_model(self):
        if self.whisper_model is None:
            try:
                print("[ModelManager] Loading faster-whisper (small)...")
                from faster_whisper import WhisperModel
                self.whisper_model = WhisperModel(
                    "small", 
                    device=self.device, 
                    compute_type="float16"
                )
                print("[ModelManager] ✓ Whisper ready")
            except Exception as e:
                print(f"[ModelManager] ✗ Whisper failed: {e}")
                self.whisper_model = None
        return self.whisper_model

    def clear_cache(self):
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

    def get_vram_usage(self):
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / 1024**3
        return 0
