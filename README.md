# Whisper AI Transcription (Local + OpenAI API)

Cross-platform transcription tool with:
- Local transcription (auto-optimized backend by platform)
- Optional timestamps (segment + word level)
- Optional speaker monologues/person split (`SPEAKER_00`, `SPEAKER_01`, ...)
- Single-file and watched-folder processing
- Desktop UI (`tkinter`) for queue-based transcription
- macOS Finder Quick Actions for right-click transcription

## What is implemented

- Local mode auto-selects backend:
  - macOS: `mlx-whisper` (Metal) if installed
  - other systems: `openai-whisper` on best device (`cuda` -> `mps` -> `cpu`)
- On macOS, if `mlx-whisper` is missing, script asks to install it automatically.
- OpenAI API mode supports:
  - `gpt-4o-transcribe-diarize` (speaker split)
  - `gpt-4o-transcribe`
  - `gpt-4o-mini-transcribe`
- Optional timestamps toggle (`y/n`) per run.
- Optional local "transcribe by persons" mode on macOS. Audio stays local; the app downloads/uses an MLX diarization model.
- Progress bar is shown in local mode (per file progress via Whisper/MLX internals).
- Russian supported via multilingual models (`small`, `medium`, `large-v3`).

## Requirements

- Python 3.11+
- `ffmpeg`
- macOS file dialog support (`tkinter`)

Python packages:
- Required: `pydub`, `watchdog`, `tkinterdnd2`
- Local Whisper fallback/CUDA path: `openai-whisper`, `torch`
- macOS optimized path: `mlx-whisper` (optional, but recommended)
- macOS local speaker split: `mlx-audio` (optional)
- OpenAI API mode: `openai` (optional)

## Installation

```bash
git clone https://github.com/tolmme/Whisper-AI.git
cd Whisper-AI
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install pydub watchdog tkinterdnd2 openai-whisper torch
```

Install ffmpeg:
- macOS: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt-get install ffmpeg`
- Windows: install ffmpeg and add it to `PATH`

Optional packages:

```bash
# macOS optimized local backend
pip install -U mlx-whisper

# macOS local speaker/person split
pip install -U mlx-audio

# OpenAI API mode
pip install -U openai
```

## Usage

GUI mode (recommended):

```bash
source venv/bin/activate
python app_gui.py
```

CLI mode:

```bash
source venv/bin/activate
python main.py
```

Then choose:
1. Single file mode or watched folder mode
2. Timestamps enabled/disabled
3. Source:
   - Local (offline, auto backend)
   - OpenAI API
4. Model

## GUI features

- Add files / add folder with audio files
- Drag and drop files or folders into the queue
- Optional "Transcribe by persons" checkbox for anonymous speaker monologues
- Queue view with statuses (`Queued`, `Processing`, `Done`, `Error`)
- Start / Stop-after-current controls
- Queue progress bar + current file indicator
- Real-time log panel
- Open selected file folder

## macOS Finder Quick Actions

Install right-click actions:

```bash
tools/macos/install_finder_services.zsh
```

This installs:
- `Transcribe Audio`
- `Transcribe Audio by Persons`

They appear in Finder's right-click menu under `Quick Actions` / `Services` for audio and video files. If macOS does not refresh immediately, relaunch Finder.

The person split action runs locally through `skill/scripts/transcribe.py --persons`.

## Russian language models

For Russian, use multilingual models:
- `small`
- `medium` (recommended balance)
- `large-v3` (best quality, slower)

Do not use `.en` models for Russian (`small.en`, `medium.en` are English-only).

## Output files

Always saved:
- Main transcript text file (with duration/model/symbol/time in filename)

Saved only when timestamps are enabled:
- Segment timestamps: `*_timestamps_model-...txt`
- Word timestamps: `*_words_model-...txt` (if available)
- Full raw result JSON: `*_full_result_model-...json`

If speaker/person split is enabled:
- Speaker monologues: `*_speakers_model-...txt`
- Speaker labels are also included in timestamp/word files when available.

## Environment variables

- `OPENAI_API_KEY` - required for OpenAI API mode
- `WHISPER_CPU_THREADS` - optional CPU thread override for local CPU mode
- `MLX_WHISPER_REPO` - optional custom MLX model repo override
- `MLX_DIARIZATION_MODEL` - optional custom MLX diarization model repo override

## Notes

- OpenAI API mode currently does not expose detailed per-segment server progress; local backends do show progress bars.
- Batch progress in queue mode is shown as `X of Y files`.

## License

MIT. See [LICENSE](LICENSE).
