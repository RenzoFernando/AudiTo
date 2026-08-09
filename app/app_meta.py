from __future__ import annotations

import os
from datetime import datetime

APP_NAME_INTERNAL = "AudiTo"
APP_DISPLAY_NAME = "AudiTo"
APP_VERSION = "3.1.0"
APP_AUTHOR = "Renzo Fernando Mosquera Daza"
APP_VENDOR_NAME = "APPS_RenzoFernando"
APP_COMPANY_NAME = APP_AUTHOR
APP_PUBLISHER_NAME = APP_COMPANY_NAME
APP_PRODUCT_NAME = APP_DISPLAY_NAME
APP_FILE_DESCRIPTION = "Aplicacion de escritorio para transcripcion local de audio a texto con Faster-Whisper."
APP_TRADEMARK = APP_DISPLAY_NAME
APP_REPOSITORY_URL = "https://github.com/RenzoFernando/AudiTo.git"
APP_REPOSITORY_WEB_URL = APP_REPOSITORY_URL[:-4] if APP_REPOSITORY_URL.endswith(".git") else APP_REPOSITORY_URL
APP_PUBLISHER_URL = APP_REPOSITORY_WEB_URL
APP_SUPPORT_URL = APP_REPOSITORY_WEB_URL
APP_UPDATES_URL = f"{APP_REPOSITORY_WEB_URL}/releases/latest"
APP_EXECUTABLE_NAME = f"{APP_NAME_INTERNAL}.exe"
APP_INSTALLER_NAME = f"{APP_NAME_INTERNAL}-Setup.exe"
APP_INSTALLER_BASENAME = os.path.splitext(APP_INSTALLER_NAME)[0]
APP_PORTABLE_ARTIFACT_NAME = f"{APP_NAME_INTERNAL}-Portable.exe"
APP_OUTPUT_DIR_NAME = "downloads"
APP_ASSETS_DIR_NAME = "assets"
APP_ICON_ICO_RELATIVE_PATH = os.path.join(APP_ASSETS_DIR_NAME, "icon.ico")
APP_INSTALL_MARKER_FILE = ".audito_installed"
APP_DATA_ROOT_DIR_NAME = APP_VENDOR_NAME
APP_DATA_APP_DIR_NAME = APP_NAME_INTERNAL


def get_current_year() -> int:
    return datetime.now().year


def get_windows_version(value: str | None = None) -> str:
    raw_value = str(value or APP_VERSION).strip()
    raw_parts = [part.strip() for part in raw_value.split(".")]
    normalized_parts: list[str] = []
    for part in raw_parts:
        if not part:
            continue
        digits_only = "".join(ch for ch in part if ch.isdigit())
        normalized_parts.append(digits_only or "0")
        if len(normalized_parts) == 4:
            break
    while len(normalized_parts) < 4:
        normalized_parts.append("0")
    return ".".join(normalized_parts)


def get_legal_copyright_text() -> str:
    return f"Copyright {get_current_year()} - {APP_AUTHOR} - All Rights Reserved."


APP_FILE_VERSION = get_windows_version(APP_VERSION)
APP_PRODUCT_VERSION = get_windows_version(APP_VERSION)
APP_LEGAL_COPYRIGHT = get_legal_copyright_text()
