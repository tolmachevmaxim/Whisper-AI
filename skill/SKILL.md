---
name: transcribe
description: Local audio transcription (mlx-whisper on Mac). Use for transcribing voice recordings, meetings, podcasts. Batch queue with progress.
allowed-tools: Bash(*)
---

# Transcribe

Local audio transcription via mlx-whisper (Metal) with openai-whisper fallback.

## Quick Commands

```bash
# Single file (default: medium model, no timestamps)
python3 skill/scripts/transcribe.py /path/to/audio.m4a

# With timestamps (for video editing)
python3 skill/scripts/transcribe.py /path/to/audio.m4a --timestamps

# Split transcript into anonymous speaker monologues (local on Mac)
python3 skill/scripts/transcribe.py /path/to/audio.m4a --persons

# Speaker monologues plus debug timestamp/json files
python3 skill/scripts/transcribe.py /path/to/audio.m4a --persons --all-outputs

# Batch with custom output dir
python3 skill/scripts/transcribe.py file1.m4a file2.mp3 -o /output/dir

# Check queue progress
python3 skill/scripts/transcribe.py --progress

# Large model for best quality
python3 skill/scripts/transcribe.py /path/to/audio.m4a --model large-v3
```

Options: `--model` (small/medium/large-v3), `--timestamps`, `--persons`/`--speakers`/`--diarize`, `--all-outputs`, `-o`/`--output-dir`, `--progress`, `--add` (add to running queue)

Speaker split is local and anonymous: output uses labels like `SPEAKER_00`.
By default `--persons` saves only `*_speakers_model-...txt`.
On macOS it uses `mlx-audio` diarization and does not upload audio.

Full docs: README.md
