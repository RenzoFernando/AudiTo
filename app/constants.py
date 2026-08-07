from __future__ import annotations

APP_NAME = "AudiTo"
APP_VERSION = "3.0.2"
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
DEFAULT_UI_LANGUAGE = "es"
GITHUB_URL = "https://github.com/RenzoFernando/AudiTo"
CONFIG_VERSION = 3
LIVE_INITIAL_SECONDS = 30.0
LIVE_CHUNK_SECONDS = 30.0
LIVE_OVERLAP_SECONDS = 2.5
LIVE_BUFFER_MAX_SECONDS = 300.0
WINDOW_WIDTH = 490
WINDOW_HEIGHT = 570
