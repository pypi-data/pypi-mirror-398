# Connexity SDK for Pipecat

A Python SDK for tracking and analyzing voice AI call sessions with Pipecat. Provides frame observers for Twilio and Daily.co integrations to capture conversation data, latency metrics, and call analytics.

## Installation

```bash
pip install connexity
```

## Version

```python
from connexity import __version__
print(__version__)
```

## Usage

### Twilio Observer

Use `ConnexityTwilioObserver` for Twilio-based telephony calls:

```python
from pipecat.audio.vad.vad_analyzer import VADParams
from connexity.pipecat.twilio import ConnexityTwilioObserver
from connexity.utils.logging_config import LogLevel
from twilio.rest import Client

# Configure VAD parameters
vad_params = VADParams(
    confidence=0.5,
    min_volume=0.6,
    start_secs=0.2,
    stop_secs=0.8,
)

# Initialize Twilio client and start recording
twilio_client = Client(account_sid, auth_token)
twilio_client.calls(call_sid).recordings.create()

# Create and initialize the observer
observer = ConnexityTwilioObserver()
await observer.initialize(
    sid=call_sid,                         # Twilio Call SID
    agent_id="YOUR_AGENT_ID",             # Your Connexity agent ID
    api_key="YOUR_CONNEXITY_API_KEY",     # Your Connexity API key
    vad_params=vad_params,                # VAD configuration
    run_mode="production",                # "development" or "production"
    vad_analyzer="silero",                # VAD engine name
    twilio_client=twilio_client,          # Twilio REST client instance
    log_level=LogLevel.INFO,              # Optional: DEBUG, INFO, WARNING, ERROR, CRITICAL
    latency_threshold_ms=4000.0,          # Optional: latency alert threshold
)

# Register with your Pipecat pipeline
pipeline.register_observer(observer)
```

### Daily.co Observer

Use `ConnexityDailyObserver` for Daily.co-based WebRTC calls:

```python
from pipecat.audio.vad.vad_analyzer import VADParams
from connexity.pipecat.daily import ConnexityDailyObserver
from connexity.utils.logging_config import LogLevel

# Configure VAD parameters
vad_params = VADParams(
    confidence=0.5,
    min_volume=0.6,
    start_secs=0.2,
    stop_secs=0.8,
)

# Create and initialize the observer
observer = ConnexityDailyObserver()
await observer.initialize(
    sid=room_name,                        # Daily.co room name/ID
    agent_id="YOUR_AGENT_ID",             # Your Connexity agent ID
    api_key="YOUR_CONNEXITY_API_KEY",     # Your Connexity API key
    vad_params=vad_params,                # VAD configuration
    run_mode="production",                # "development" or "production"
    vad_analyzer="silero",                # VAD engine name
    daily_api_key="YOUR_DAILY_API_KEY",   # Daily.co API key (required)
    log_level=LogLevel.INFO,              # Optional: DEBUG, INFO, WARNING, ERROR, CRITICAL
    latency_threshold_ms=4000.0,          # Optional: latency alert threshold
)
# Note: Daily.co calls are always treated as "web" type with no phone numbers

# Register with your Pipecat pipeline
pipeline.register_observer(observer)
```

### Tool Observer

Use `@observe_tool` decorator to monitor and track tool function executions:

```python
from connexity.pipecat import observe_tool
from pipecat.services.llm_service import FunctionCallParams
from typing import Dict

@observe_tool(
    tool_name="end_call",              # Optional: explicit tool name
    include_result=True,                # Optional: capture return value (default: True)
    include_traceback=True,            # Optional: capture tracebacks on errors (default: True)
    enable_timeout=True,               # Optional: enforce execution timeout (default: True)
    timeout_seconds=10.0,              # Optional: timeout duration in seconds (default: 10.0)
)
async def end_call(params: FunctionCallParams) -> Dict[str, str]:
    # Your tool implementation
    return {"status": "ended", "sid": call_sid}
```

The decorator automatically tracks:
- Execution timing and duration
- Tool call IDs and arguments
- Success/failure status
- Error detection in results
- Timeout enforcement
- Callback invocation tracking

## Logging Configuration

The SDK uses a centralized logging system that can be configured globally:

```python
from connexity.utils.logging_config import set_sdk_log_level, LogLevel

# Set log level for all SDK components
set_sdk_log_level(LogLevel.DEBUG)
```

Available log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## Features

- **Conversation Capture**: Records user/assistant messages with timing
- **Latency Tracking**: Measures STT, LLM, TTS, and end-to-end latency
- **Interruption Detection**: Identifies unsuccessful user interruptions and interruption loops
- **Tool Call Monitoring**: Tracks function call lifecycle and issues
- **Issue Reporting**: Automatically reports latency peaks and errors
- **System Prompt Extraction**: Captures and analyzes system prompts
- **Recording Integration**: Retrieves call recordings from Twilio/Daily.co

---

# CHANGELOG

## v1.0.0 — 2025-12-22

### New Features

- **SDK Version Management**
  Added `__version__` in connexity init for library version tracking. SDK version is now sent to gateway with all API calls.

- **Centralized Logging Configuration**
  Added configurable logging system with `LogLevel` enum and `set_sdk_log_level()` function. Replaced `verbose` parameter with `log_level` for granular control (DEBUG, INFO, WARNING, ERROR, CRITICAL).

- **Enhanced DocStrings**
  Updated all files with comprehensive DocStrings describing purposes of files, classes, functions, and methods. Added default types to all variables in function signatures.

- **Improved Issue Tracking**
  Renamed internal "errors and incidents" to "issues" for consistency (exception: Pipecat ErrorFrames retained for navigation). All gateway interactions now use unified "Issues" terminology.

- **STT/TTS/LLM Detailed Tracking**
  Added detailed data capture for STT, TTS, and LLM services in `CallSessionData` class, including provider and model information.

### Breaking Changes

- **Unified `run_mode` Parameter**
  Replaced `env` parameter with `run_mode` everywhere. Update all `env="development"` to `run_mode="development"`.

- **Observer Initialization Signatures Updated**
  - `ConnexityTwilioObserver.initialize()` now only accepts `twilio_client` (not `daily_api_key`)
  - `ConnexityDailyObserver.initialize()` now only accepts `daily_api_key` (not `twilio_client`)
  - Removed `voice_engine` from init signatures (auto-detected per observer type)
  - Removed `phone_call_provider` from init signatures (auto-set based on observer)

- **Removed Deprecated Attributes**
  - Removed `transcriber` attribute, replaced with `stt_*` attributes
  - Removed `voice_provider` attribute, replaced with `tts_*` attributes
  - Removed unused `stream` variable from `client.register_call()` init

- **Logging Changes**
  - Removed `_log()` method from observer interface
  - Replaced `verbose` parameter with `log_level`
  - All logging now uses centralized configuration

### Internal Improvements

- **Performance Optimizations**
  - Made regexes precompiled for efficiency
  - Made `REDACT_KEYS_EXACT` frozenset for O(1) lookups
  - Made `REDACT_VALUE_PATTERNS` tuple for faster iteration
  - Created module-level frozenset constants for token matching
  - Made `_ERROR_SOURCE_PATTERNS` module-level Final[dict] for single allocation

- **Code Quality**
  - Extracted long Literals from function signatures for readability
  - Added `NotImplementedError` to `BaseMessage.to_dict()` to force implementation
  - Added comments for complex tasks, removed redundant comments
  - Normalized `CONSTS.py` naming to `consts.py`
  - Removed redundant env loading in consts
  - Added `format-fix` command to Makefile
  - Added autoflake and ruff to pyproject.toml

- **Observer Architecture**
  - Added `_setup_common()` method in `BaseConnexityObserver` for shared initialization logic
  - Improved logging with detailed messages sorted by importance levels

- **Module Reorganization**
  - Moved pipecat files to `connexity/pipecat/` module
  - Renamed files to shorter names (`base_observer.py`, `twilio.py`, `daily.py`)
  - Renamed `InterfaceConnexityObserver` to `BaseConnexityObserver`
  - Moved utility files to `connexity/pipecat/utils/`
  - Renamed `connexity/metrics` to `connexity/elevenlabs` (not exposed in package exports)
  - Added missing `__init__.py` for `connexity/pipecat/utils`

- **Call Session Management**
  - Added `CallSession` class to manage call data and lifecycle
  - Added Pydantic models (`CallSessionData`, `ServiceSegment`) for type safety
  - Added `connexity_api` utility for gateway communication
  - Removed `base_call.py` and `send_data.py` (functionality moved to new structure)

- **Development Tooling**
  - Added ruff linter configuration to pyproject.toml
  - Added Makefile with lint, format, and check targets using uv
  - Added `requires-python >=3.11` to pyproject.toml
  - Added `uv.lock` to `.gitignore`
  - Applied ruff auto-fixes to codebase

---

## v0.0.8.19 — 2025-11-27

### New Features

- **Latency Peaks Improved**
- **Tool Call Incidents Improved**

---

## v0.0.8.18 — 2025-11-09

### New Features

- **Interruption Loop Incident Added**
- **Added System Prompts Pulling** to create prompt-based incidents

---

## v0.0.8.17 — 2025-11-07

### New Features

- **Pipecat Tool Calls Incident Added**

---

## v0.0.8.16 — 2025-11-06

- **Hotfix**

---

## v0.0.8.15 — 2025-11-06

### New Features

- **Observability Improvements**
  Refactored how Pipecat errors are handled

- **Interruption Incident Added**

---

## v0.0.8.13 — 2025-10-24

### New Features

- **snapshot_error_frame.py**
  Added wrapper to capture error frames in Pipecat

---

## v0.0.8.12 — 2025-09-04

### Critical Fix

- **get_daily_recording_url**
  Fixed issue with types

---

## v0.0.8.11 — 2025-09-02

### New Features

- **ConnexityDailyObserver Support**
  Added support for `ConnexityDailyObserver`, including retrieving Daily recording and call duration.
  **Note:** You must pass `daily_api_key` to enable this feature.

- **STT and TTS Model Parameters**
  - `stt_model`: Specify the speech-to-text model to use
  - `tts_model`: Specify the text-to-speech model to use
  - `tts_voice`: Specify the voice ID for text-to-speech

### Breaking Changes

- **Observer Logic Refactor**
  - Introduced `BaseConnexityObserver` with standardized `initialize()` and `on_push_frame()` methods
  - Created `ConnexityDailyObserver` and `ConnexityTwilioObserver` as separate classes

---

## v0.0.8.9 — 2025-06-24

### Minor Fixes

- **Get recording from region-specific Twilio account**

---

## v0.0.8.8 — 2025-06-24

### Breaking Changes

- **Twilio DI Instead of Credentials**
  Removed `twilio_account_sid` and `twilio_auth_token` parameters from `initialize()`.
  Now you must pass a `twilio_client: Client` instance via the `twilio_client` argument.
  **Action required:** Construct and start your own Twilio Client, then inject it into the observer.

---

## v0.0.8.7 — 2025-06-20

### Breaking Changes

- **Removed Built-in Twilio Call Recording**
  Recording is no longer performed by this package.
  **Action required:** Start your Twilio recording on the app side as soon as the WebSocket connection is established.

---

## v0.0.8.6 — 2025-06-13

### New Features

- **VAD Compensation**
  - Configurable via `VADParams`
  - Pass `vad_params` into `initialize()`
  - Added `run_mode` and `vad_analyzer` metadata fields to `register_call`