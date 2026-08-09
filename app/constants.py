from __future__ import annotations

from app.app_meta import APP_DISPLAY_NAME, APP_REPOSITORY_WEB_URL, APP_VERSION

APP_NAME = APP_DISPLAY_NAME
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
GITHUB_URL = APP_REPOSITORY_WEB_URL
CONFIG_VERSION = 4
LIVE_INITIAL_SECONDS = 60.0
LIVE_CHUNK_SECONDS = 60.0
LIVE_OVERLAP_SECONDS = 2.5
LIVE_BUFFER_MAX_SECONDS = 300.0
WINDOW_WIDTH = 490
WINDOW_HEIGHT = 570
