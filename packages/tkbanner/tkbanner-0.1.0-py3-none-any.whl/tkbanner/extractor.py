import subprocess
from PIL import Image

# ====================================================
# 🟦 КАДРИ (відео)
# ====================================================
def extract_frames(video_path, width=None, height=None, fps=None):
    """
    Зчитує відео з FFmpeg і повертає генератор кадрів (PIL.Image)
    у форматі RGB без збереження на диск.
    Якщо fps=None — використовується FPS самого відео.
    """
    args = [
        "ffmpeg",
        "-i", video_path,
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-vcodec", "rawvideo",
        "-loglevel", "quiet",
    ]

    # масштабування
    if width and height:
        args.extend(["-vf", f"scale={width}:{height}"])
    # fps
    if fps is not None:
        args.extend(["-r", str(fps)])

    args.append("-")  # вивід у stdout

    # запускаємо ffmpeg
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**8)

    # визначаємо розмір кадру
    if not width or not height:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height", "-of", "csv=p=0", video_path],
            capture_output=True, text=True
        )
        try:
            width, height = map(int, probe.stdout.strip().split(','))
        except Exception:
            process.stdout.close()
            process.wait()
            return

    frame_size = width * height * 3

    # послідовно читаємо кадри
    while True:
        raw = process.stdout.read(frame_size)
        if not raw or len(raw) < frame_size:
            break
        frame = Image.frombytes("RGB", (width, height), raw)
        yield frame

    process.stdout.close()
    process.wait()


# ====================================================
# 🟨 СИРИЙ АУДІОПОТІК (PCM)
# ====================================================
def extract_audio_bytes(video_path, sample_rate=44100, channels=2):
    """
    Повертає генератор сирих аудіо-байтів із відео (float32 PCM).
    Це можна напряму подавати в sounddevice або будь-яку іншу бібліотеку.
    """
    args = [
        "ffmpeg",
        "-i", video_path,
        "-f", "f32le",            # 32-бітний float PCM
        "-acodec", "pcm_f32le",
        "-ar", str(sample_rate),  # частота дискретизації
        "-ac", str(channels),     # кількість каналів
        "-vn",                    # вимикаємо відео
        "-loglevel", "quiet",
        "-"
    ]

    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**8)
    chunk_size = 4096 * channels * 4  # 4096 семплів (float32 = 4 байти)
    while True:
        raw = process.stdout.read(chunk_size)
        if not raw:
            break
        yield raw

    process.stdout.close()
    process.wait()


# ====================================================
# 🟩 ДОПОМІЖНА ФУНКЦІЯ
# ====================================================
def get_video_info(video_path):
    """
    Отримує базову інформацію про відео: ширину, висоту, fps, тривалість.
    """
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate,duration",
         "-of", "csv=p=0", video_path],
        capture_output=True, text=True
    )
    try:
        width, height, fps_str, duration = probe.stdout.strip().split(',')
        num, den = map(int, fps_str.split('/'))
        fps = num / den if den != 0 else 0
        return {
            "width": int(width),
            "height": int(height),
            "fps": fps,
            "duration": float(duration)
        }
    except Exception:
        return None
