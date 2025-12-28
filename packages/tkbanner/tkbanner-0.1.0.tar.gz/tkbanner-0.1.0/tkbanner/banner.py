import threading
import time
from PIL import ImageTk
import tkinter as tk

from .extractor import extract_frames, extract_audio_bytes, get_video_info

# опціональні залежності для звуку
try:
    import numpy as np
    import sounddevice as sd
    _AUDIO_SUPPORTED = True
except Exception:
    _AUDIO_SUPPORTED = False


class VideoBanner(tk.Label):
    def __init__(self, master, video_path, fps=None, delay=None,
                 loop=False, one_frame = False,
                 on_click=None, lazy_loading = False, width=None, height=None, prebuffer=4,
                 music=False, audio_samplerate=44100, audio_channels=2):
        super().__init__(master)

        self.video_path = video_path
        info = get_video_info(video_path) or {}
        self.fps = fps if fps is not None else info.get("fps", 0) or 0
        self.delay = delay if delay is not None else (int(1000 / self.fps) if self.fps > 0 else 40)
        self.loop = loop
        self.on_click = on_click
        self.width = width or info.get("width")
        self.height = height or info.get("height")
        self.prebuffer = max(1, prebuffer)
        self.one_frame = one_frame
        self.lazy_loading = lazy_loading

        self.music = bool(music) and _AUDIO_SUPPORTED
        if music and not _AUDIO_SUPPORTED:
            print("Warning: sounddevice or numpy not available — music disabled")
        self.sample_rate = int(audio_samplerate)
        self.channels = int(audio_channels)

        # frame buffer
        self.frames = []
        self._frame_lock = threading.Lock()
        self.current_frame_index = 0
        self.running = False

        # streaming threads/flags
        self._after_id = None
        self._stream_thread = None
        self._stream_stop = threading.Event()
        self._stream_done = False

        # audio buffer & playback
        self._audio_buffer = None         # numpy array shape (n_samples, channels)
        self._audio_loaded = False
        self._audio_lock = threading.Lock()
        self._audio_loader_thread = None
        self._audio_stop_event = threading.Event()
        self._audio_stream = None         # sounddevice.OutputStream
        self._audio_pos = 0               # current play position in samples (int)
        self.one_frame_1 = one_frame

        # audio master time
        self._audio_start_time = None     # perf_counter time when audio position 0 corresponds to start

        if self.on_click:
            self.bind("<Button-1>", lambda e: self.on_click())

        # start loading frames (and audio loader if requested)
        self._start_streaming()
        if self.music:
            self._start_audio_loader()

    # ---------------- streaming frames ----------------
    def _start_streaming(self):
        self._stream_stop.clear()
        self._stream_done = False
        with self._frame_lock:
            self.frames = []
        self.current_frame_index = 0
        if self.lazy_loading:
            self._stream_thread = threading.Thread(target=self._stream_worker, daemon=True)
            self._stream_thread.start()
        else:
            self._stream_worker()
    def _stream_worker(self):
        try:
            gen = extract_frames(self.video_path, width=self.width, height=self.height, fps=self.fps)
        except Exception:
            self._stream_done = True
            return

        for pil in gen:
            if self._stream_stop.is_set():
                break
            try:
                pil = pil.convert('RGB')
                photo = ImageTk.PhotoImage(pil)
            except Exception:
                continue
            with self._frame_lock:
                self.frames.append(photo)
                if self.one_frame_1 and self.running is False:
                    self.config(image=self.frames[0])
                    self._first_frame_shown = False
                    self.one_frame_1 = False

        self._stream_done = True

    def close_stream(self):
        self._stream_stop.set()
        thread = self._stream_thread
        self._stream_thread = None
        if thread and thread.is_alive():
            thread.join(timeout=0.5)
        # stop audio components
        self._stop_audio_stream()
        self._stop_audio_loader()

    # ---------------- audio loader / buffer ----------------
    def _start_audio_loader(self):
        if not _AUDIO_SUPPORTED:
            return
        self._audio_stop_event.clear()
        # ensure previous loader stopped
        self._stop_audio_loader()
        if self.lazy_loading:
            self._audio_loader_thread = threading.Thread(target=self._audio_loader_worker, daemon=True)
            self._audio_loader_thread.start()
        else:
            self._audio_loader_worker()

    def _stop_audio_loader(self):
        if self._audio_loader_thread:
            self._audio_stop_event.set()
            self._audio_loader_thread.join(timeout=0.2)
            self._audio_loader_thread = None
            with self._audio_lock:
                self._audio_loaded = False
                self._audio_buffer = None

    def _audio_loader_worker(self):
        """Завантажує все аудіо у numpy buffer (float32) у фоновому режимі."""
        try:
            chunks = []
            for chunk in extract_audio_bytes(self.video_path, sample_rate=self.sample_rate, channels=self.channels):
                if self._audio_stop_event.is_set():
                    break
                if not chunk:
                    break
                chunks.append(chunk)
            if not chunks:
                return
            raw = b"".join(chunks)
            # конвертація у numpy float32
            arr = np.frombuffer(raw, dtype=np.float32)
            if self.channels > 1:
                arr = arr.reshape(-1, self.channels)
            else:
                arr = arr.reshape(-1, 1)
            with self._audio_lock:
                self._audio_buffer = arr.copy()
                self._audio_loaded = True
                # clamp audio pos
                self._audio_pos = max(0, min(int(self._audio_pos), self._audio_buffer.shape[0] - 1))
            # якщо вже відтворення йде — почати аудіопотік
            if self.running:
                self._start_audio_stream()
        except Exception as e:
            print("Audio loader error:", e)
            with self._audio_lock:
                self._audio_buffer = None
                self._audio_loaded = False

    # ---------------- audio stream (playback) ----------------
    def _audio_callback(self, outdata, frames, time_info, status):
        """sounddevice callback: заповнює outdata з буфера, вихід float32."""
        with self._audio_lock:
            if not self._audio_loaded or self._audio_buffer is None:
                outdata.fill(0)
                return
            buf = self._audio_buffer
            start = int(self._audio_pos)
            end = start + frames
            if start >= buf.shape[0]:
                outdata.fill(0)
                self._audio_pos = buf.shape[0]
                return
            if end <= buf.shape[0]:
                out = buf[start:end]
                self._audio_pos = end
            else:
                out = buf[start:buf.shape[0]]
                pad = np.zeros((frames - out.shape[0], buf.shape[1]), dtype=buf.dtype)
                out = np.vstack([out, pad])
                self._audio_pos = buf.shape[0]
            outdata[:] = out

    def _start_audio_stream(self):
        if not _AUDIO_SUPPORTED:
            return
        with self._audio_lock:
            if not self._audio_loaded:
                return
        if self._audio_stream is None:
            try:
                # start stream and set audio_start_time so wall-clock matches audio_pos
                self._audio_stream = sd.OutputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype='float32',
                    callback=self._audio_callback,
                    blocksize=1024
                )
                self._audio_stream.start()
                # set _audio_start_time according to current _audio_pos
                with self._audio_lock:
                    pos = int(self._audio_pos)
                self._audio_start_time = time.perf_counter() - (pos / float(self.sample_rate))
            except Exception as e:
                print("Failed to start audio stream:", e)
                self._audio_stream = None

    def _stop_audio_stream(self):
        if self._audio_stream is not None:
            try:
                self._audio_stream.stop()
                self._audio_stream.close()
            except Exception:
                pass
            self._audio_stream = None
        # keep buffer loaded but clear master time
        self._audio_start_time = None

    def _set_audio_pos_from_frame(self, frame_index):
        """Встановлює позицію відтворення (в семплах) відповідно до кадру."""
        if not self.music or not _AUDIO_SUPPORTED:
            return
        if not self.fps or self.fps <= 0:
            sec = 0.0
        else:
            sec = frame_index / float(self.fps)
        sample = int(sec * self.sample_rate)
        with self._audio_lock:
            if self._audio_loaded and self._audio_buffer is not None:
                sample = max(0, min(sample, self._audio_buffer.shape[0] - 1))
            else:
                sample = max(0, sample)
            self._audio_pos = sample
            # adjust master clock so that perf_counter->frame mapping stays consistent
            self._audio_start_time = time.perf_counter() - (self._audio_pos / float(self.sample_rate))

    # ---------------- navigation / seek ----------------
    
    def start_audio(self):
        self._set_audio_pos_from_frame(self.current_frame_index)
        if self._audio_loaded:
            self._start_audio_stream()
    
    def stop_audio(self):
        if self.music and _AUDIO_SUPPORTED:
            self._stop_audio_stream()
    
    def left(self, step=1):
        with self._frame_lock:
            if len(self.frames) == 0:
                return
            self.current_frame_index = max(0, self.current_frame_index - abs(step))
            frame = self.frames[self.current_frame_index]
        self.config(image=frame)
        if self.music and _AUDIO_SUPPORTED:
            # update audio pos and master time, do not stop stream
            self._set_audio_pos_from_frame(self.current_frame_index)
            # if stream exists but wasn't started because audio not loaded earlier, ensure start when loaded

    def right(self, step=1):
        with self._frame_lock:
            if len(self.frames) == 0:
                return
            self.current_frame_index = min(len(self.frames) - 1, self.current_frame_index + abs(step))
            frame = self.frames[self.current_frame_index]
        self.config(image=frame)
        if self.music and _AUDIO_SUPPORTED:
            self._set_audio_pos_from_frame(self.current_frame_index)

    def to_switch(self, index):
        with self._frame_lock:
            if len(self.frames) == 0:
                return
            idx = int(index)
            idx = max(0, min(len(self.frames) - 1, idx))
            self.current_frame_index = idx
            frame = self.frames[self.current_frame_index]
        self.config(image=frame)
        if self.music and _AUDIO_SUPPORTED:
            self._set_audio_pos_from_frame(self.current_frame_index)

    # ---------------- controls ----------------
    def start(self):
        if self.running:
            return
        self.running = True
        # If music enabled and buffer loaded: set audio pos according to current frame
        if self.music and _AUDIO_SUPPORTED:
            self._set_audio_pos_from_frame(self.current_frame_index)
            if self._audio_loaded:
                self._start_audio_stream()
        # start the frame update loop (frames will be chosen by audio time when audio_active)
        self._update_frame()

    def stop(self):
        self.running = False
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        # stop audio playback (but keep buffer loaded)
        if self.music and _AUDIO_SUPPORTED:
            self._stop_audio_stream()

    def set_banner(self, video_path=None, fps=None, on_click=None, lazy_loading = None, width=None, height=None, prebuffer=None):
        # зупиняємо і очищуємо
        set_banner_is_True = False
        if video_path is not None or fps is not None or width is not None or height is not None or prebuffer is not None:
            self.close_stream()
            if self.running and self.music:
                self.stop()
            with self._frame_lock:
                self.frames = []
            self.current_frame_index = 0
            set_banner_is_True = True

        if video_path is not None:
            self.video_path = video_path
        if fps is not None:
            self.fps = fps
            self.delay = int(1000 / fps) if fps > 0 else self.delay
        if on_click is not None:
            self.on_click = on_click
        if lazy_loading is not None:
            self.lazy_loading = lazy_loading
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        if prebuffer is not None:
            self.prebuffer = max(1, prebuffer)

        if self.on_click:
            self.bind("<Button-1>", lambda e: self.on_click())
        if set_banner_is_True:
            self._start_streaming()
            if self.music:
                self._start_audio_loader()

    # ---------------- playback loop (audio-driven when possible) ----------------
    def _update_frame(self):
        if not self.running:
            return

        # compute desired frame index based on master time
        desired_idx = None
        if self.music and _AUDIO_SUPPORTED and self._audio_start_time is not None:
            # audio-driven: derive frame from master clock
            elapsed = time.perf_counter() - self._audio_start_time
            desired_idx = int(elapsed * self.fps) if self.fps > 0 else int(elapsed * (1000.0 / self.delay))
        else:
            # fallback: internal timer based on after scheduling
            desired_idx = self.current_frame_index + 1

        with self._frame_lock:
            total = len(self.frames)

        if total == 0:
            # still no frames — wait
            self._after_id = self.after(self.delay, self._update_frame)
            return

        # handle end-of-stream / looping
        if desired_idx >= total:
            if self._stream_done:
                if self.loop:
                    if total > 0:
                        desired_idx = desired_idx % total
                    else:
                        desired_idx = 0
                    if self.music and _AUDIO_SUPPORTED:
                        self._stop_audio_stream()
                        self._set_audio_pos_from_frame(self.current_frame_index)
                        if self._audio_loaded:
                            self._start_audio_stream()
                else:
                    self.stop()
                    return
            else:
                # audio is ahead of loaded frames — clamp to last available
                desired_idx = total - 1

        # update current frame and display
        with self._frame_lock:
            # clamp
            idx = desired_idx
            frame = self.frames[idx]
            self.current_frame_index = idx

        self.config(image=frame)
        
        if self.music and _AUDIO_SUPPORTED and self._audio_start_time is not None and self.fps > 0:
            # calculate next frame wall-clock time
            now = time.perf_counter()
            next_frame_time = self._audio_start_time + (self.current_frame_index + 1) / float(self.fps)
            delay_ms = max(1, int((next_frame_time - now) * 1000))
        else:
            delay_ms = max(1, int(self.delay))

        # schedule next update — small interval for smoothness
        self._after_id = self.after(self.delay, self._update_frame)

    def destroy(self):
        self.close_stream()
        self.stop()
        super().destroy()
