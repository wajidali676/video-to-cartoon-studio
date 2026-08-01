import cv2
import os
import subprocess
import shutil
import numpy as np

def get_video_info(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0
    cap.release()
    return {"fps": fps, "total_frames": total_frames, "width": width,
            "height": height, "duration": duration}

def has_audio(video_path):
    try:
        cmd = ["ffprobe", "-v", "error", "-select_streams", "a:0",
               "-show_entries", "stream=codec_type", "-of", "default=noprint_wrappers=1", video_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return "codec_type=audio" in result.stdout
    except:
        return False

def extract_audio(video_path, output_audio_path):
    if not has_audio(video_path):
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
               "-t", "1", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", output_audio_path]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", output_audio_path]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

def segment_video(video_path, output_dir, segment_duration=5):
    os.makedirs(output_dir, exist_ok=True)
    info = get_video_info(video_path)
    duration = info["duration"]
    segments = []
    start = 0
    idx = 0
    while start < duration:
        end = min(start + segment_duration, duration)
        seg_path = os.path.join(output_dir, f"segment_{idx:04d}.mp4")
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-ss", str(start), "-to", str(end),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            seg_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        segments.append(seg_path)
        start = end
        idx += 1
    return segments

def process_segment(input_path, output_path, cartoonizer, flip=False, aesthetic="none"):
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    width = width if width % 2 == 0 else width - 1
    height = height if height % 2 == 0 else height - 1
    
    temp_avi = output_path.replace(".mp4", "_temp.avi")
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(temp_avi, fourcc, fps, (width, height))
    
    if not out.isOpened():
        cap.release()
        raise RuntimeError("Failed to create VideoWriter")
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if flip:
            frame = cv2.flip(frame, 1)
        
        processed = cartoonizer.process_frame(frame, aesthetic)
        
        if processed.shape[:2] != (height, width):
            processed = cv2.resize(processed, (width, height), interpolation=cv2.INTER_LANCZOS4)
        
        if processed.dtype != np.uint8:
            processed = np.clip(processed, 0, 255).astype(np.uint8)
        
        out.write(processed)
        frame_count += 1
        del frame
    
    cap.release()
    out.release()
    
    if frame_count == 0:
        raise RuntimeError("No frames written!")
    
    cmd = [
        "ffmpeg", "-y", "-i", temp_avi,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-an",
        output_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if os.path.exists(temp_avi):
        os.remove(temp_avi)
    
    if not os.path.exists(output_path) or os.path.getsize(output_path) < 1000:
        raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()[:500]}")
    
    return frame_count

def combine_segments(segment_paths, output_path, audio_path=None):
    list_file = os.path.join(os.path.dirname(output_path), "concat_list.txt")
    with open(list_file, "w") as f:
        for seg in segment_paths:
            f.write(f"file '{seg}'\n")
    
    if audio_path and os.path.exists(audio_path):
        temp_video = output_path.replace(".mp4", "_temp.mp4")
        cmd1 = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", list_file, "-c", "copy", temp_video
        ]
        subprocess.run(cmd1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        cmd2 = [
            "ffmpeg", "-y", "-i", temp_video, "-i", audio_path,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            "-shortest", output_path
        ]
        subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        os.remove(temp_video)
    else:
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", list_file, "-c", "copy",
            "-movflags", "+faststart",
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    
    os.remove(list_file)
    
    if not os.path.exists(output_path) or os.path.getsize(output_path) < 1000:
        raise RuntimeError("Final video is empty!")
