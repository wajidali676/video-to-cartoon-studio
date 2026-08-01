"""
Video to Cartoon Studio — FastAPI Backend
Kaggle Optimized (P100 16GB VRAM)
"""
import os
import sys
import shutil
import json
import time
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import *
from model_loader import ModelManager
from cartoonizer import Cartoonizer
from video_utils import *
from voice_processor import VoiceProcessor

app = FastAPI(title="Video to Cartoon Studio")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

model_mgr = ModelManager()
voice_proc = VoiceProcessor(model_mgr)

# In-memory job history
job_history = []

def add_to_history(job_id, filename, style, status, download_url_no_voice=None, download_url_with_voice=None):
    job_history.insert(0, {
        "job_id": job_id,
        "filename": filename,
        "style": style,
        "status": status,
        "timestamp": time.strftime("%H:%M:%S"),
        "download_url_no_voice": download_url_no_voice,
        "download_url_with_voice": download_url_with_voice
    })
    while len(job_history) > 20:
        job_history.pop()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/ui", response_class=HTMLResponse)
async def ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_video(video: UploadFile = File(...)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, video.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(video.file, f)
    info = get_video_info(file_path)
    return JSONResponse({
        "success": True,
        "filename": video.filename,
        "duration": round(info["duration"], 2),
        "resolution": f"{info['width']}x{info['height']}",
        "fps": info["fps"]
    })

@app.post("/process")
async def process_video(
    filename: str = Form(...),
    style: str = Form("cartoon"),
    segment_duration: int = Form(5),
    voice_option: str = Form("original"),
    language: str = Form("en"),
    pitch: int = Form(0),
    mirror_flip: bool = Form(False),
    aesthetic: str = Form("none"),
    tts_text: str = Form("")
):
    try:
        input_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(input_path):
            return JSONResponse({"error": "File not found"}, status_code=404)
        info = get_video_info(input_path)
        if info["duration"] > MAX_VIDEO_DURATION:
            return JSONResponse({"error": f"Video too long. Max {MAX_VIDEO_DURATION}s"}, status_code=400)
        job_id = f"{Path(filename).stem}_{int(time.time())}"
        job_dir = os.path.join(OUTPUT_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)

        audio_path = os.path.join(job_dir, "original_audio.wav")
        extract_audio(input_path, audio_path)

        final_audio = audio_path
        if voice_option == "original" and pitch != 0:
            pitched_audio = os.path.join(job_dir, "pitched_audio.wav")
            voice_proc.change_pitch(audio_path, pitched_audio, pitch)
            final_audio = pitched_audio
        elif voice_option == "tts" and tts_text.strip():
            tts_audio = os.path.join(job_dir, "tts_audio.mp3")
            voice_proc.text_to_speech_sync(tts_text.strip(), tts_audio, language)
            final_audio = tts_audio
        elif voice_option == "extract":
            text = voice_proc.extract_text(audio_path)
            if text:
                tts_audio = os.path.join(job_dir, "extracted_tts.mp3")
                voice_proc.text_to_speech_sync(text, tts_audio, language)
                final_audio = tts_audio

        seg_dir = os.path.join(job_dir, "segments")
        segments = segment_video(input_path, seg_dir, segment_duration)

        cartoonizer = Cartoonizer(style=style, device=model_mgr.device)
        if style in ["anime", "3d_render"]:
            cartoonizer.set_model(model_mgr.load_anime_model())

        processed_dir = os.path.join(job_dir, "processed")
        os.makedirs(processed_dir, exist_ok=True)
        processed_segments = []

        for idx, seg_path in enumerate(segments):
            flip = mirror_flip and (idx % 2 == 1)
            out_path = os.path.join(processed_dir, f"proc_{idx:04d}.mp4")
            process_segment(seg_path, out_path, cartoonizer, flip=flip, aesthetic=aesthetic)
            processed_segments.append(out_path)
            if idx % CLEAR_CACHE_EVERY == 0:
                model_mgr.clear_cache()

        final_video_no_voice = os.path.join(job_dir, f"{job_id}_no_voice.mp4")
        combine_segments(processed_segments, final_video_no_voice, None)

        final_video_with_voice = os.path.join(job_dir, f"{job_id}_with_voice.mp4")
        combine_segments(processed_segments, final_video_with_voice, final_audio)

        shutil.rmtree(seg_dir, ignore_errors=True)
        shutil.rmtree(processed_dir, ignore_errors=True)

        url_no_voice = f"/download/{job_id}/{job_id}_no_voice.mp4"
        url_with_voice = f"/download/{job_id}/{job_id}_with_voice.mp4"

        add_to_history(job_id, filename, style, "completed", url_no_voice, url_with_voice)

        return JSONResponse({
            "success": True,
            "job_id": job_id,
            "download_url_no_voice": url_no_voice,
            "download_url_with_voice": url_with_voice,
            "duration": info["duration"],
            "segments": len(segments)
        })
    except Exception as e:
        import traceback
        add_to_history(job_id if 'job_id' in locals() else "error", filename if 'filename' in locals() else "unknown", style if 'style' in locals() else "unknown", "failed")
        return JSONResponse({"error": str(e), "detail": traceback.format_exc()}, status_code=500)

@app.get("/download/{job_id}/{filename}")
async def download(job_id: str, filename: str):
    file_path = os.path.join(OUTPUT_DIR, job_id, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4", filename=filename)
    return JSONResponse({"error": "File not found"}, status_code=404)

@app.get("/history")
async def get_history():
    return JSONResponse({"history": job_history})

@app.get("/vram")
async def vram_status():
    usage = model_mgr.get_vram_usage()
    return JSONResponse({"allocated_gb": round(usage, 2), "total_gb": 16.0, "free_gb": round(16.0 - usage, 2)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
