from __future__ import annotations

import sys
from pathlib import Path

from app import app_meta


def _version_tuple(value: str) -> tuple[int, int, int, int]:
    parts = [int(part) for part in value.split(".")]
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def _escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("'", "\\'")


def main() -> int:
    output_path = Path(sys.argv[1] if len(sys.argv) > 1 else ".build_version_info.txt")
    file_version = _version_tuple(app_meta.APP_FILE_VERSION)
    product_version = _version_tuple(app_meta.APP_PRODUCT_VERSION)
    text = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={file_version},
    prodvers={product_version},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('CompanyName', '{_escape(app_meta.APP_COMPANY_NAME)}'),
            StringStruct('FileDescription', '{_escape(app_meta.APP_FILE_DESCRIPTION)}'),
            StringStruct('FileVersion', '{_escape(app_meta.APP_FILE_VERSION)}'),
            StringStruct('InternalName', '{_escape(app_meta.APP_NAME_INTERNAL)}'),
            StringStruct('LegalCopyright', '{_escape(app_meta.APP_LEGAL_COPYRIGHT)}'),
            StringStruct('LegalTrademarks', '{_escape(app_meta.APP_TRADEMARK)}'),
            StringStruct('OriginalFilename', '{_escape(app_meta.APP_EXECUTABLE_NAME)}'),
            StringStruct('ProductName', '{_escape(app_meta.APP_PRODUCT_NAME)}'),
            StringStruct('ProductVersion', '{_escape(app_meta.APP_PRODUCT_VERSION)}')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    output_path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
