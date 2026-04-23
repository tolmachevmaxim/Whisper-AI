"""Local speaker diarization helpers.

The default backend uses mlx-audio Sortformer on Apple Silicon. It runs locally
and returns anonymous speaker labels (SPEAKER_00, SPEAKER_01, ...).
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from typing import Any

from pydub import AudioSegment


DEFAULT_MLX_DIARIZATION_MODEL = "mlx-community/diar_sortformer_4spk-v1-fp16"


@dataclass
class SpeakerTurn:
    start: float
    end: float
    speaker: str


def _attr_or_key(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _normalise_speaker_label(value: Any) -> str:
    raw = str(value if value is not None else "0").strip()
    if raw.upper().startswith("SPEAKER_"):
        return raw.upper()
    if raw.isdigit():
        return f"SPEAKER_{int(raw):02d}"
    return raw or "SPEAKER_00"


def _extract_turns(result: Any) -> list[SpeakerTurn]:
    raw_segments = _attr_or_key(result, "segments", []) or []
    turns: list[SpeakerTurn] = []
    for item in raw_segments:
        start = _attr_or_key(item, "start")
        end = _attr_or_key(item, "end")
        speaker = _attr_or_key(item, "speaker", "0")
        if start is None or end is None:
            continue
        start_f = float(start)
        end_f = float(end)
        if end_f <= start_f:
            continue
        turns.append(
            SpeakerTurn(
                start=start_f,
                end=end_f,
                speaker=_normalise_speaker_label(speaker),
            )
        )
    return sorted(turns, key=lambda turn: (turn.start, turn.end))


def _export_temp_wav(file_path: str) -> str:
    """Export input to 16 kHz mono wav for diarization backend compatibility."""
    audio = AudioSegment.from_file(file_path).set_channels(1).set_frame_rate(16000)
    fd, tmp_path = tempfile.mkstemp(suffix=".wav", prefix="whisper_diarization_")
    os.close(fd)
    audio.export(tmp_path, format="wav")
    return tmp_path


def run_mlx_diarization(
    file_path: str,
    model_repo: str | None = None,
    threshold: float = 0.5,
) -> list[SpeakerTurn]:
    """Run local MLX diarization and return anonymous speaker turns."""
    try:
        from mlx_audio.vad import load
    except ImportError as import_error:
        raise RuntimeError(
            "Local speaker diarization requires mlx-audio. "
            "Install it with: pip install -U mlx-audio"
        ) from import_error

    repo = model_repo or os.getenv(
        "MLX_DIARIZATION_MODEL",
        DEFAULT_MLX_DIARIZATION_MODEL,
    )
    wav_path = _export_temp_wav(file_path)
    try:
        print(f"Local speaker diarization: mlx-audio, model: {repo}")
        model = load(repo)
        result = model.generate(wav_path, threshold=threshold, verbose=True)
        turns = _extract_turns(result)
    finally:
        try:
            os.remove(wav_path)
        except OSError:
            pass

    if not turns:
        raise RuntimeError("Speaker diarization finished but returned no speaker turns.")
    return turns


def _overlap_seconds(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def _speaker_for_span(turns: list[SpeakerTurn], start: float, end: float) -> str | None:
    if not turns:
        return None

    best_turn = None
    best_overlap = 0.0
    for turn in turns:
        overlap = _overlap_seconds(start, end, turn.start, turn.end)
        if overlap > best_overlap:
            best_turn = turn
            best_overlap = overlap
    if best_turn is not None and best_overlap > 0:
        return best_turn.speaker

    midpoint = (start + end) / 2
    nearest = min(
        turns,
        key=lambda turn: min(abs(midpoint - turn.start), abs(midpoint - turn.end)),
    )
    return nearest.speaker


def add_speaker_labels(result: dict[str, Any], turns: list[SpeakerTurn]) -> dict[str, Any]:
    """Attach speaker labels to Whisper segment and word timestamps."""
    for segment in result.get("segments", []) or []:
        seg_start = float(segment.get("start", 0) or 0)
        seg_end = float(segment.get("end", seg_start) or seg_start)
        speaker = _speaker_for_span(turns, seg_start, seg_end)
        if speaker:
            segment["speaker"] = speaker

        for word in segment.get("words", []) or []:
            word_start = float(word.get("start", seg_start) or seg_start)
            word_end = float(word.get("end", word_start) or word_start)
            word_speaker = _speaker_for_span(turns, word_start, word_end) or speaker
            if word_speaker:
                word["speaker"] = word_speaker

    result["speaker_turns"] = [
        {"start": turn.start, "end": turn.end, "speaker": turn.speaker}
        for turn in turns
    ]
    return result


def build_speaker_monologues(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Build consecutive speaker monologues from word timestamps if available."""
    monologues: list[dict[str, Any]] = []

    for segment in result.get("segments", []) or []:
        words = segment.get("words", []) or []
        if words:
            for word in words:
                text = (word.get("word") or "").strip()
                if not text:
                    continue
                speaker = word.get("speaker") or segment.get("speaker") or "UNKNOWN"
                start = float(word.get("start", segment.get("start", 0)) or 0)
                end = float(word.get("end", start) or start)
                if monologues and monologues[-1]["speaker"] == speaker:
                    monologues[-1]["end"] = end
                    monologues[-1]["text"] = f"{monologues[-1]['text']} {text}".strip()
                else:
                    monologues.append(
                        {"speaker": speaker, "start": start, "end": end, "text": text}
                    )
            continue

        text = (segment.get("text") or "").strip()
        if not text:
            continue
        speaker = segment.get("speaker") or "UNKNOWN"
        start = float(segment.get("start", 0) or 0)
        end = float(segment.get("end", start) or start)
        if monologues and monologues[-1]["speaker"] == speaker:
            monologues[-1]["end"] = end
            monologues[-1]["text"] = f"{monologues[-1]['text']} {text}".strip()
        else:
            monologues.append(
                {"speaker": speaker, "start": start, "end": end, "text": text}
            )

    return monologues
