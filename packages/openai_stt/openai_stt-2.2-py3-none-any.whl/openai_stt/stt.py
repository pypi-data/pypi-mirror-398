from __future__ import annotations

from typing import Any, Callable, Literal
import os
import time
import wave
import tempfile
import collections
from collections.abc import Iterable
import warnings
import logging
import weakref
import atexit

import pyaudio
import webrtcvad
import keyboard as kb

from syntaxmod.general import wait_until
from openai import OpenAI

# Quiet the spam
warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
for name in ["whisper", "transformers", "numba"]:
    logging.getLogger(name).setLevel(logging.ERROR)


def cuda_available() -> bool:
    import ctypes

    for name in ("nvcuda.dll", "libcuda.so", "libcuda.dylib"):
        try:
            return ctypes.CDLL(name).cuInit(0) == 0
        except Exception:
            continue
    return False


_USE_FASTER = True
_HAS_CUDA = False

try:
    from faster_whisper import WhisperModel as FWModel  # type: ignore
except Exception:
    _USE_FASTER = False
    import whisper  # type: ignore

    try:
        _HAS_CUDA = cuda_available()
    except Exception:
        _HAS_CUDA = False


TranscriptionMode = Literal["faster-whisper", "whisper", "api"]


class STT:
    """
    Library-friendly behavior:
    - No need to call close() after each record call (auto-closes audio by default).
    - Still supports `with STT() as stt:` if you want manual control.
    - Safe cleanup at process exit and on GC as a backup.
    """

    @staticmethod
    def _cleanup_audio(stream: Any, p: Any) -> None:
        try:
            if stream is not None:
                try:
                    if getattr(stream, "is_active", lambda: False)():
                        stream.stop_stream()
                except Exception:
                    pass
                try:
                    stream.close()
                except Exception:
                    pass
        finally:
            if p is not None:
                try:
                    p.terminate()
                except Exception:
                    pass

    @staticmethod
    def _finalize(self_ref: "weakref.ReferenceType[STT]") -> None:
        obj = self_ref()
        if obj is None:
            return
        try:
            obj.close()
        except Exception:
            pass

    def __init__(
        self,
        model: Literal[
            "tiny.en",
            "tiny",
            "base.en",
            "base",
            "small.en",
            "small",
            "medium.en",
            "medium",
            "large-v1",
            "large-v2",
            "large-v3",
            "large",
            "large-v3-turbo",
            "turbo",
            "whisper-1",
            "gpt-4o-transcribe",
            "gpt-4o-mini-transcribe",
        ] = "base",
        aggressive: int = 2,
        chunk_duration_ms: int = 30,
        preroll_ms: int = 300,
        tail_silence_ms: int = 600,
        min_record_ms: int = 400,
        api_key: str | None = None,
        api_model: str | None = None,
        default_transcription_mode: TranscriptionMode | None = None,
        auto_close_audio: bool = True,
    ):
        assert chunk_duration_ms in (10, 20, 30)

        self.rate = 16000
        self.chunk_ms = chunk_duration_ms
        self.chunk = int(self.rate * self.chunk_ms / 1000)

        self.preroll_chunks = max(1, int(preroll_ms / self.chunk_ms))
        self.tail_silence_chunks = max(1, int(tail_silence_ms / self.chunk_ms))
        self.min_record_chunks = max(1, int(min_record_ms / self.chunk_ms))

        self.auto_close_audio = auto_close_audio
        self._shutdown = False

        # Audio is lazily opened per recording call
        self.p: pyaudio.PyAudio | None = None
        self.stream: Any | None = None
        self._sampwidth: int = 2  # updated when audio opens

        # Backup cleanup on exit and GC
        self._finalizer = weakref.finalize(self, STT._finalize, weakref.ref(self))
        atexit.register(self._finalizer)

        # VAD
        self.vad = webrtcvad.Vad(aggressive)

        # Model + client
        remote_only_models = {
            "whisper-1",
            "gpt-4o-transcribe",
            "gpt-4o-mini-transcribe",
        }

        self._local_model = None
        self.client: OpenAI | None = None
        self._api_model_name = api_model or "whisper-1"

        resolved_key: str | None = None
        if isinstance(api_key, str) and api_key:
            resolved_key = api_key
        elif api_key is None:
            env_key = os.getenv("OPENAI_API_KEY")
            if env_key:
                resolved_key = env_key

        if resolved_key:
            self.client = OpenAI(api_key=resolved_key)

        if model in remote_only_models:
            self.backend = "api"
            self._default_transcription_mode: TranscriptionMode = "api"
            self._api_model_name = api_model or model
        else:
            self.backend = "faster" if _USE_FASTER else "whisper"
            self._default_transcription_mode = (
                "faster-whisper" if self.backend == "faster" else "whisper"
            )

            model_root = os.path.join(tempfile.gettempdir(), "whisper_models")
            if self.backend == "faster":
                self._local_model = FWModel(
                    model,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=max(2, os.cpu_count() or 4),
                    download_root=model_root,
                )
            else:
                device = "cuda" if _HAS_CUDA else "cpu"
                self._local_model = whisper.load_model(
                    model,
                    download_root=model_root,
                    device=device,
                )

        if default_transcription_mode is not None:
            self._default_transcription_mode = default_transcription_mode

    def __enter__(self) -> "STT":
        # If you use context manager, you likely want to keep audio open across calls
        self.auto_close_audio = False
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    # ---------- audio lifecycle ----------

    def _open_audio(self) -> None:
        if self._shutdown:
            raise RuntimeError("STT is shutdown. Create a new STT() instance.")
        if self.stream is not None and self.p is not None:
            return

        self.p = pyaudio.PyAudio()
        self._sampwidth = self.p.get_sample_size(pyaudio.paInt16)
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
        )

    def close(self) -> None:
        # Closes only the audio resources. The instance can be used again (it will re-open audio lazily).
        if self.stream is None and self.p is None:
            return
        try:
            STT._cleanup_audio(self.stream, self.p)
        finally:
            self.stream = None
            self.p = None

    def shutdown(self) -> None:
        # Permanent close (optional)
        self._shutdown = True
        self.close()

    # ---------- internals ----------

    def _save_wav_temp(self, frames: list[bytes]) -> str:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.close()  # important on Windows to avoid file locking
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self._sampwidth)
            wf.setframerate(self.rate)
            wf.writeframes(b"".join(frames))
        return tmp.name

    def _fw_transcribe_file(self, filename: str) -> str:
        if self._local_model is None:
            raise RuntimeError("Faster-whisper backend is not initialized.")
        try:
            segments, _ = self._local_model.transcribe(
                filename,
                beam_size=1,
                temperature=0.0,
                vad_filter=False,
                language="en",
            )
        except TypeError:
            segments, _ = self._local_model.transcribe(
                filename,
                beam_size=1,
                temperature=0.0,
                vad_filter=False,
                language="en",
            )
        return "".join(seg.text for seg in segments).strip()  # type: ignore

    def _whisper_transcribe_file(self, filename: str) -> str:
        if self._local_model is None:
            raise RuntimeError("Whisper backend is not initialized.")
        result = self._local_model.transcribe(  # type: ignore[attr-defined]
            filename,
            temperature=0.0,
            condition_on_previous_text=False,
            language="en",
        )
        return str(result.get("text", "")).strip()

    def _api_transcribe_file(self, filename: str) -> str:
        if self.client is None:
            raise RuntimeError(
                "API transcription requested but no OpenAI client is initialized. "
                "Provide api_key or set OPENAI_API_KEY."
            )
        with open(filename, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(  # type: ignore[attr-defined]
                model=self._api_model_name,
                file=audio_file,
            )
        text = getattr(response, "text", None)
        if text is None and isinstance(response, dict):
            text = response.get("text")
        if text is None:
            raise RuntimeError("Transcription response missing text field from API.")
        return str(text).strip()

    def _transcribe_file_with_mode(self, filename: str, mode: TranscriptionMode) -> str:
        if mode == "faster-whisper":
            if self.backend != "faster" or self._local_model is None:
                raise RuntimeError("Faster-whisper mode requested but not available.")
            return self._fw_transcribe_file(filename)

        if mode == "whisper":
            if self.backend != "whisper" or self._local_model is None:
                raise RuntimeError("Whisper mode requested but not available.")
            return self._whisper_transcribe_file(filename)

        if mode == "api":
            return self._api_transcribe_file(filename)

        raise ValueError(f"Unknown transcription mode: {mode}")

    def _resolve_transcription_mode(
        self, mode: TranscriptionMode | None
    ) -> TranscriptionMode:
        return (
            mode
            if mode is not None
            else getattr(self, "_default_transcription_mode", "whisper")
        )

    def _transcribe_frames(
        self, frames: list[bytes], mode: TranscriptionMode | None = None
    ) -> str:
        if not frames:
            return ""
        filename = self._save_wav_temp(frames)
        try:
            resolved_mode = self._resolve_transcription_mode(mode)
            return self._transcribe_file_with_mode(filename, resolved_mode)
        finally:
            try:
                os.remove(filename)
            except Exception:
                pass

    def _collect_frames(
        self,
        *,
        min_appended_chunks: int | None = None,
        max_read_chunks: int | None = None,
        stop_condition: Callable[[dict[str, Any]], bool] | None = None,
        on_chunk: (
            Callable[
                [bytes, list[bytes], dict[str, Any]], bytes | Iterable[bytes] | None
            ]
            | None
        ) = None,
        context: dict[str, Any] | None = None,
    ) -> list[bytes]:
        self._open_audio()

        frames: list[bytes] = []
        ctx = dict(context or {})
        ctx.setdefault("read_chunks", 0)
        ctx.setdefault("appended_chunks", 0)

        min_required = (
            self.min_record_chunks
            if min_appended_chunks is None
            else min_appended_chunks
        )

        while True:
            # stream is guaranteed open here
            data = self.stream.read(self.chunk, exception_on_overflow=False)  # type: ignore[union-attr]
            ctx["read_chunks"] += 1

            result = on_chunk(data, frames, ctx) if on_chunk else data

            appended = 0
            if result is None:
                pass
            elif isinstance(result, (bytes, bytearray)):
                frames.append(bytes(result))
                appended = 1
            elif isinstance(result, Iterable):
                new_frames: list[bytes] = []
                for chunk in result:
                    if not isinstance(chunk, (bytes, bytearray)):
                        raise TypeError(
                            "on_chunk must return bytes or an iterable of bytes, got "
                            f"{type(chunk)!r}"
                        )
                    new_frames.append(bytes(chunk))
                frames.extend(new_frames)
                appended = len(new_frames)
            else:
                raise TypeError(
                    "on_chunk must return bytes, an iterable of bytes, or None, got "
                    f"{type(result)!r}"
                )

            ctx["appended_chunks"] += appended

            if max_read_chunks is not None and ctx["read_chunks"] >= max_read_chunks:
                break

            if ctx["appended_chunks"] < min_required:
                continue

            if stop_condition is not None and stop_condition(ctx):
                break

        return frames

    def _record_then_transcribe(
        self,
        collect_fn: Callable[[], list[bytes]],
        mode: TranscriptionMode | None,
        log_done_msg: str | None = None,
    ) -> str:
        try:
            frames = collect_fn()
            text = self._transcribe_frames(frames, mode=mode)
            if log_done_msg:
                print(log_done_msg)
            return text
        finally:
            if self.auto_close_audio:
                self.close()

    # ---------- public APIs ----------

    def record_for_seconds(
        self,
        duration: float = 5.0,
        log: bool = False,
        mode: TranscriptionMode | None = None,
    ) -> str:
        if log:
            print(f"Recording for {duration} seconds...")
        total_chunks = max(1, int((duration * 1000) / self.chunk_ms))

        def collect() -> list[bytes]:
            return self._collect_frames(
                max_read_chunks=total_chunks, min_appended_chunks=0
            )

        return self._record_then_transcribe(
            collect, mode, log_done_msg="Done." if log else None
        )

    def record_with_keyboard(
        self,
        key: str = "space",
        log: bool = False,
        mode: TranscriptionMode | None = None,
    ) -> str:
        if log:
            print(f"Press {key} to arm. Release to start recording.")
        kb.wait(key)
        while kb.is_pressed(key):
            time.sleep(0.01)

        if log:
            print(f"Recording... Press {key} again to stop.")

        def stop_condition(_: dict[str, Any]) -> bool:
            if kb.is_pressed(key):
                while kb.is_pressed(key):
                    time.sleep(0.01)
                return True
            return False

        def collect() -> list[bytes]:
            return self._collect_frames(
                stop_condition=stop_condition,
                min_appended_chunks=self.min_record_chunks,
            )

        return self._record_then_transcribe(
            collect, mode, log_done_msg="Stopped." if log else None
        )

    def record_with_vad(
        self,
        log: bool = False,
        mode: TranscriptionMode | None = None,
    ) -> str:
        ring: collections.deque[bytes] = collections.deque(maxlen=self.preroll_chunks)
        state: dict[str, Any] = {"triggered": False, "silence_streak": 0}

        if log:
            print("Listening...")

        def on_chunk(
            data: bytes, _frames: list[bytes], ctx: dict[str, Any]
        ) -> bytes | list[bytes] | None:
            is_speech = self.vad.is_speech(data, self.rate)

            if not state["triggered"]:
                ring.append(data)
                if is_speech:
                    state["triggered"] = True
                    state["silence_streak"] = 0
                    ctx["triggered"] = True
                    if log:
                        print("Speech started.")
                    buffered = list(ring)
                    ring.clear()
                    return buffered
                return []

            if is_speech:
                state["silence_streak"] = 0
            else:
                state["silence_streak"] += 1

            ctx["triggered"] = True
            ctx["silence_streak"] = state["silence_streak"]
            return data

        def stop_condition(ctx: dict[str, Any]) -> bool:
            return (
                bool(ctx.get("triggered"))
                and int(ctx.get("silence_streak", 0)) >= self.tail_silence_chunks
            )

        def collect() -> list[bytes]:
            return self._collect_frames(
                on_chunk=on_chunk,
                stop_condition=stop_condition,
                min_appended_chunks=self.min_record_chunks,
            )

        return self._record_then_transcribe(
            collect, mode, log_done_msg="Speech ended." if log else None
        )

    def record_with_callback_or_bool(
        self,
        callback_or_bool: Callable[[], bool] | bool,
        log: bool = False,
        mode: TranscriptionMode | None = None,
    ) -> str:
        # Callable behavior:
        # - Wait until callback() becomes True
        # - Record while it stays True
        # - Stop once it becomes False (after min duration gate)
        #
        # Bool behavior:
        # - True -> use VAD
        # - False -> do nothing

        if isinstance(callback_or_bool, bool):
            if not callback_or_bool:
                return ""
            return self.record_with_vad(log=log, mode=mode)

        cond = callback_or_bool

        if log:
            print("Waiting for callback to become True...")
        wait_until(cond)

        if log:
            print("Recording while callback stays True...")

        def on_chunk(data: bytes, _frames: list[bytes], _ctx: dict[str, Any]) -> bytes:
            return data

        def stop_condition(_ctx: dict[str, Any]) -> bool:
            try:
                return not bool(cond())
            except Exception:
                return True

        def collect() -> list[bytes]:
            return self._collect_frames(
                on_chunk=on_chunk,
                stop_condition=stop_condition,
                min_appended_chunks=self.min_record_chunks,
            )

        return self._record_then_transcribe(
            collect, mode, log_done_msg="Stopped." if log else None
        )

    def transcribe_file(
        self, audio_file: str, mode: TranscriptionMode | None = None
    ) -> str:
        resolved = self._resolve_transcription_mode(mode)
        return self._transcribe_file_with_mode(audio_file, resolved)


if __name__ == "__main__":
    stt = STT(model="base", auto_close_audio=True)
    print(stt.record_with_keyboard(log=True))
