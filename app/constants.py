from __future__ import annotations

APP_NAME = "AudiTo"
APP_VERSION = "0.6.0"
SUPPORTED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".m4a",
    ".wav",
    ".aac",
    ".flac",
    ".ogg",
    ".opus",
    ".wma",
    ".aiff",
    ".amr",
}
LANGUAGES = {
    "Español": "es",
    "Inglés": "en",
    "Automático": None,
}
DEFAULT_LANGUAGE = "Español"
DEFAULT_PROFILE = "Equilibrada"
CONFIG_VERSION = 2
LIVE_INITIAL_SECONDS = 30.0
LIVE_CHUNK_SECONDS = 30.0
LIVE_OVERLAP_SECONDS = 2.5
LIVE_BUFFER_MAX_SECONDS = 300.0
WINDOW_WIDTH = 490
WINDOW_HEIGHT = 570
