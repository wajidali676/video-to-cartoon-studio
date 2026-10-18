# Video to Cartoon Studio

Video to Cartoon Studio is a local web application for turning short videos into stylized clips. It provides a browser-based workflow for choosing a visual style, adjusting the audio, and downloading the processed video.

## Problem Statement

Applying a consistent illustrated look to a video, adjusting its appearance, and preparing an alternate voice track can require several separate editing tools. That workflow can be difficult to reproduce, especially for users who want a straightforward way to process a short clip.

## Solution

The application runs a FastAPI server on your computer and provides a web interface for uploading a video and selecting processing options. It processes the video in segments and frames, then combines the results into downloadable MP4 files. The project is also prepared for GPU-backed use on Kaggle; see [KAGGLE_SETUP.md](KAGGLE_SETUP.md) for those instructions.

## Models and Processing

- **Anime:** Uses the AnimeGAN2 generator, downloaded through PyTorch Hub on first use.
- **Cartoon, 3D Render, Sketch, Watercolor, and aesthetic filters:** Implemented with OpenCV image-processing operations. The 3D Render effect is an image-processing effect, not a separate learned 3D model.
- **Extract and Replace voice:** Uses faster-whisper's small speech-recognition model to transcribe audio, then Edge-TTS to synthesize speech in the selected voice. The text is not automatically translated.
- **Text to Speech:** Sends the text to Edge-TTS to generate speech in the selected language.

AnimeGAN2 and faster-whisper models may need to download the first time they are used. Edge-TTS requires an internet connection.

## Features

- Five visual styles: Cartoon, Anime, 3D Render, Sketch, and Watercolor.
- Original audio with an adjustable pitch, speech transcription and re-voicing, or typed text-to-speech.
- Voice options for English, Urdu, Hindi, Arabic, Spanish, French, German, Chinese, Japanese, and Korean.
- Optional Vintage, Bright, Dramatic, Soft, and Cinematic filters.
- Optional alternating mirror flips and adjustable segment duration.
- Separate downloads for video without audio and video with the selected audio.
- Frame-by-frame processing that retains the input video's resolution.

## Requirements

- Python 3.10-3.12.
- FFmpeg, with both `ffmpeg` and `ffprobe` available on your system `PATH`. See the [FFmpeg download page](https://ffmpeg.org/download.html).
- PyTorch and torchvision, installed separately from `requirements.txt`.
- An NVIDIA GPU with a compatible CUDA-enabled PyTorch build is recommended. The application can select CPU when CUDA is unavailable, but processing may be considerably slower. Speech recognition is configured for GPU use.
- Internet access for downloading models and using Edge-TTS.

For PyTorch, select a build that matches your operating system and hardware at [pytorch.org](https://pytorch.org/get-started/locally/). The following CUDA 12.1 command is the version documented for the Kaggle P100 setup:

```powershell
python -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu121
```

## Run on Your Computer

Open a terminal in the project folder and create a virtual environment.

**Windows PowerShell:**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS or Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

With the environment active, install a suitable PyTorch build as described above, then install the remaining dependencies and start the server:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

Open [http://127.0.0.1:8000/ui](http://127.0.0.1:8000/ui) in your browser. Keep the terminal and server running while using the application.

## How to Use

1. Upload an MP4, MOV, or AVI video. The application accepts videos up to 500 MB and processes videos up to 60 seconds long.
2. Choose a visual style and, optionally, an aesthetic filter, segment duration, or alternating mirror flip.
3. Choose the audio option: retain the original voice and optionally change its pitch, transcribe and re-voice it, or enter text for text-to-speech. Select a language when using generated speech.
4. Select **Start Processing** and wait for the job to finish.
5. Download the result with the selected audio or the video without audio.

Uploaded videos and generated files are stored in the project's `static/uploads` and `static/outputs` folders, respectively.

## Kaggle Setup

For the GPU-backed Kaggle workflow, including its notebook and public-link setup, see [KAGGLE_SETUP.md](KAGGLE_SETUP.md).
