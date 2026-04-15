# Nova v2 (Local-First AI VTuber Foundation)
Nova v2 extends the existing local chatbot into a lightweight VTuber foundation:
- Local GGUF LLM via `llama-cpp-python`
- Local voice output via Piper TTS
- Lightweight heuristic emotion detection
- Optional VTube Studio integration via `pyvts`

Everything is local-first and works with CPU fallback.
## Quickstart (v2)
1. Install dependencies from `requirements.txt`.
2. Copy `.env.example` to `.env`.
3. Set `MODEL_PATH` to your local GGUF model path.
4. Optional: enable TTS (`TTS_ENABLED=true`) and set `TTS_MODEL_PATH`.
5. Optional: enable avatar integration (`AVATAR_ENABLED=true`) and open VTube Studio.
6. Run `python3 main.py`.

## Features
- CLI chat loop (kept from v1)
- Personality + memory system (kept from v1)
- Emotion tagging from assistant output (`happy`, `thinking`, `neutral`, `playful`, `serious`)
- Automatic TTS after every assistant response
- Optional avatar expression and idle trigger hooks

## Project structure
```text
novaV2/
├── main.py
├── config.py
├── model.py
├── personality.py
├── memory.py
├── chat.py
├── emotion.py
├── tts.py
├── avatar.py
├── requirements.txt
├── .env.example
├── README.md
├── models/
├── voices/
└── logs/
```

## Requirements
- Python 3.10+
- Local GGUF model file
- Piper TTS binary (for voice output)
- Optional: VTube Studio + `pyvts` (for avatar control)

## Installation
### Linux
```bash
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -r requirements.txt
```

### Windows (PowerShell)
```powershell
py -m pip install --upgrade pip setuptools wheel
py -m pip install -r requirements.txt
```

## Setup
1. Copy environment template:

### Linux
```bash
cp .env.example .env
```

### Windows (PowerShell)
```powershell
Copy-Item .env.example .env
```

2. Ensure folders exist:

### Linux
```bash
mkdir -p models voices logs
```

### Windows (PowerShell)
```powershell
New-Item -ItemType Directory -Force models, voices, logs | Out-Null
```

3. Set your LLM GGUF path in `.env`:
```dotenv
MODEL_PATH=models/Qwen2.5-3B-Instruct-Q4_K_M.gguf
```

## Version 2: TTS setup (Piper)
1. Install Piper CLI (platform package/binary).
2. Download a Piper voice model (`.onnx`) and its JSON config.
3. Put voice files under `voices/`, for example:
   - `voices/en_US-lessac-medium.onnx`
   - `voices/en_US-lessac-medium.onnx.json`
4. Update `.env`:
```dotenv
TTS_ENABLED=true
TTS_MODEL_PATH=voices/en_US-lessac-medium.onnx
TTS_PLAYBACK_ENABLED=true
PIPER_BINARY=piper
```

### How to download voice models
- Voice models are available in the Piper voices repository and releases.
- Download one `.onnx` voice model and the matching `.onnx.json` file.
- Keep both files in the same directory.

## Optional VTube Studio setup
1. Start VTube Studio.
2. Enable API access in VTube Studio.
3. In `.env`, set:
```dotenv
AVATAR_ENABLED=true
```
4. Launch Nova and approve plugin auth in VTube Studio on first connect.

### Optional hotkeys in VTube Studio
If configured, Nova will attempt to trigger these hotkeys:
- `NovaHappy`
- `NovaThinking`
- `NovaNeutral`
- `NovaPlayful`
- `NovaSerious`
- `NovaIdle`

Missing hotkeys are ignored safely.

## Usage
### Smoke test
```bash
python3 main.py --smoke-test
```

### Start chat
```bash
python3 main.py
```

## Chat commands
- `/help` — show commands
- `/status` — show runtime status
- `/reset` — clear memory
- `/exit` — quit
## Runtime pipeline (v2)
`User input -> LLM response -> Emotion detection -> TTS -> Avatar reaction`

## Configuration summary
- Core runtime:
  - `MODEL_PATH`, `CHAT_FORMAT`
  - `N_CTX`, `N_THREADS`, `N_BATCH`, `N_GPU_LAYERS`
  - `TEMPERATURE`, `TOP_P`, `MAX_TOKENS`, `REPEAT_PENALTY`
  - `ALLOW_CPU_FALLBACK`
- Memory:
  - `MEMORY_MAX_TURNS`, `MEMORY_TOKEN_BUDGET`
- Logging:
  - `LOG_DIR`, `VERBOSE`
- Version 2:
  - `EMOTION_ENABLED`
  - `TTS_ENABLED`, `TTS_MODEL_PATH`, `TTS_PLAYBACK_ENABLED`, `PIPER_BINARY`
  - `AVATAR_ENABLED`

## Troubleshooting
### No audio
- Confirm `TTS_ENABLED=true`
- Confirm `TTS_PLAYBACK_ENABLED=true`
- Confirm your system audio output works
- Reinstall dependencies:
```bash
python3 -m pip install -r requirements.txt
```

### Missing TTS model
- Confirm `TTS_MODEL_PATH` points to an existing `.onnx` file
- Ensure matching `.onnx.json` is in the same directory

### Avatar not connecting
- Confirm VTube Studio is running
- Confirm API is enabled in VTube Studio
- Keep `AVATAR_ENABLED=false` if you want text+voice only mode

### Model load issues
- Set `N_GPU_LAYERS=0` for CPU mode
- Ensure `MODEL_PATH` is valid

## Performance notes
- Designed for consumer hardware and CPU fallback.
- Keep `N_CTX` and `MAX_TOKENS` moderate for low latency.
- TTS runs locally through Piper and should be near real-time for short replies.
