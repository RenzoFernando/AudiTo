
from __future__ import annotations

from app import app_meta


VALUES = {
    "APP_NAME": app_meta.APP_NAME_INTERNAL,
    "APP_EXE_NAME": app_meta.APP_EXECUTABLE_NAME,
    "ICON_FILE": app_meta.APP_ICON_ICO_RELATIVE_PATH,
    "ASSETS_FOLDER": app_meta.APP_ASSETS_DIR_NAME,
    "OUTPUT_FOLDER": app_meta.APP_OUTPUT_DIR_NAME,
    "PRODUCT_NAME": app_meta.APP_PRODUCT_NAME,
    "FILE_DESCRIPTION": app_meta.APP_FILE_DESCRIPTION,
    "PRODUCT_VERSION": app_meta.APP_PRODUCT_VERSION,
    "FILE_VERSION": app_meta.APP_FILE_VERSION,
    "COMPANY_NAME": app_meta.APP_COMPANY_NAME,
    "COPYRIGHT_TEXT": app_meta.APP_LEGAL_COPYRIGHT,
    "TRADEMARK_TEXT": app_meta.APP_TRADEMARK,
    "PORTABLE_ARTIFACT_NAME": app_meta.APP_PORTABLE_ARTIFACT_NAME,
    "LICENSE_FILE": app_meta.APP_LICENSE_RELATIVE_PATH,
    "INSTALLER_NAME": app_meta.APP_INSTALLER_NAME,
    "INSTALLER_BASENAME": app_meta.APP_INSTALLER_BASENAME,
    "PUBLISHER_URL": app_meta.APP_PUBLISHER_URL,
    "SUPPORT_URL": app_meta.APP_SUPPORT_URL,
    "UPDATES_URL": app_meta.APP_UPDATES_URL,
    "INSTALL_MARKER_FILE": app_meta.APP_INSTALL_MARKER_FILE,
}


for key, value in VALUES.items():
    text = str(value).replace('"', '')
    print(f'set "{key}={text}"')


