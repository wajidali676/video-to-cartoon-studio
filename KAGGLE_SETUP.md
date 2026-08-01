# 🎨 Video to Cartoon Studio — Kaggle Setup

## Step 1: Upload as Kaggle Dataset
1. Zip the `video_to_cartoon_studio` folder
2. Go to Kaggle → Datasets → New Dataset
3. Upload the zip file
4. Name it `video-to-cartoon-studio`

## Step 2: Create New Notebook
1. New Notebook → Add Input → Your Dataset
2. Select `video-to-cartoon-studio`

## Step 3: Install PyTorch (P100 Compatible)
Run in first cell:
```python
!pip uninstall -y torch torchvision torchaudio
!pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu121
```

## Step 4: Install Requirements
```python
!pip install -r /kaggle/input/video-to-cartoon-studio/video_to_cartoon_studio/requirements.txt
```

## Step 5: Run Server + ngrok
```python
import os, subprocess, time

# Static folder
static_path = "/kaggle/input/video-to-cartoon-studio/video_to_cartoon_studio/static"
os.makedirs(static_path, exist_ok=True)

# Copy to working (for write access)
import shutil
src = "/kaggle/input/video-to-cartoon-studio/video_to_cartoon_studio"
dst = "/kaggle/working/video_to_cartoon_studio"
if os.path.exists(dst):
    shutil.rmtree(dst)
shutil.copytree(src, dst)

# Start server
os.chdir(dst)
server = subprocess.Popen(["python", "main.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print("✅ Server started!")
time.sleep(10)

# ngrok tunnel
!pip install -q pyngrok
from pyngrok import ngrok
ngrok.kill()
public_url = ngrok.connect(8000)
print(f"🌐 URL: {public_url}/ui")
```

## Features
- ✅ 5 Styles: Cartoon, Anime (AI), 3D Render, Sketch, Watercolor
- ✅ Voice: Original pitch-shift, Extract & Replace, Text-to-Speech
- ✅ Languages: English, Urdu, Hindi, Arabic, Spanish, French, German, Chinese, Japanese, Korean
- ✅ Mirror flip alternate segments
- ✅ Aesthetic filters: Cinematic, Vintage, Bright, Dramatic, Soft
- ✅ Maintains original video resolution
- ✅ Memory efficient (processes frame-by-frame)

## GPU Requirements
- Kaggle GPU P100 (16GB VRAM) — Perfect
- 1 minute video, 5-second segments = ~12 segments
- Processing time: ~3-5 minutes for 1 minute video
