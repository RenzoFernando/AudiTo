from __future__ import annotations

APP_STYLE = """
QMainWindow, QWidget {
    background-color: #0f1115;
    color: #f3f4f6;
    font-family: "Segoe UI";
    font-size: 11px;
}
QLabel {
    background-color: transparent;
    border: none;
}
QLabel#brandLabel {
    font-size: 21px;
    font-weight: 700;
    color: #ff4655;
}
QLabel#sectionLabel {
    color: #b0b4bb;
    font-size: 10px;
    font-weight: 600;
}
QLabel#dropTitle {
    color: #f7f7f8;
    font-size: 13px;
    font-weight: 600;
}
QLabel#inputHelperLabel {
    color: #a2a7af;
    font-size: 9px;
}
QLabel#mutedLabel {
    color: #737984;
    font-size: 9px;
}
QLabel#fileNameLabel {
    color: #f4f4f5;
    font-size: 11px;
    font-weight: 600;
}
QLabel#fileMetaLabel {
    color: #9298a2;
    font-size: 9px;
}
QLabel#fileDot {
    color: #ff4655;
    font-size: 9px;
}
QLabel#fileDot[state="completed"], QLabel#fileDot[state="recorded"] {
    color: #ff6572;
}
QLabel#progressStatusLabel {
    color: #d8dade;
    font-size: 10px;
}
QLabel#progressStatusLabel[state="completed"] {
    color: #ff6572;
    font-weight: 600;
}
QLabel#progressStatusLabel[state="recording"] {
    color: #eceef1;
    font-weight: 600;
}
QLabel#etaLabel {
    color: #8b9099;
    font-size: 10px;
}
QLabel#modelHintLabel {
    color: #ff6572;
    font-size: 9px;
}
QLabel#footerLabel {
    color: #8a8f98;
    font-size: 8px;
    font-weight: 500;
}
QFrame#audioInput {
    background-color: #171a20;
    border: 1px solid #414852;
    border-radius: 6px;
}
QFrame#audioInput[dragActive="true"] {
    background-color: #1b1f25;
    border: 1px solid #ff4655;
}
QFrame#fileCard {
    background-color: #171a20;
    border: 1px solid #414852;
    border-radius: 6px;
}
QFrame#progressFrame {
    background-color: transparent;
    border: none;
}
QFrame#footerFrame {
    background-color: #171a20;
    border: none;
    border-top: 1px solid #252a31;
}
QFrame#accentRed {
    background-color: #ff4655;
    border: none;
}
QFrame#accentGrayStrong {
    background-color: #4a4f58;
    border: none;
}
QFrame#accentGraySoft {
    background-color: #2b2f36;
    border: none;
}
QPushButton {
    min-height: 30px;
    padding: 0 10px;
    border-radius: 4px;
    border: 1px solid #414852;
    background-color: #1a1e24;
    color: #eceef1;
    font-size: 10px;
}
QPushButton:hover {
    background-color: #22262d;
    border-color: #ff4655;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #171a20;
    border-color: #ff6572;
}
QPushButton:focus {
    border-color: #414852;
}
QPushButton:disabled {
    color: #5f646d;
    background-color: #14171b;
    border-color: #292f37;
}
QPushButton#languageToggleButton {
    min-width: 36px;
    max-width: 36px;
    min-height: 30px;
    max-height: 30px;
    padding: 0;
    border-radius: 4px;
    border: 1px solid #343a43;
    background-color: #15191e;
    color: #b8bdc5;
    font-size: 8px;
    font-weight: 700;
}
QPushButton#languageToggleButton:hover {
    border-color: #ff4655;
    color: #ffffff;
}
QPushButton#languageToggleButton:disabled {
    color: #5f646d;
    background-color: #14171b;
    border-color: #292f37;
}
QPushButton#footerLinkButton {
    min-height: 18px;
    max-height: 18px;
    min-width: 0;
    padding: 0 2px;
    border: none;
    border-radius: 0;
    background-color: transparent;
    color: #ff6572;
    font-size: 8px;
    font-weight: 600;
}
QPushButton#footerLinkButton:hover {
    background-color: transparent;
    border: none;
    color: #ffffff;
}
QPushButton#footerLinkButton:pressed {
    background-color: transparent;
    border: none;
    color: #ff4655;
}
QPushButton#primaryButton {
    min-height: 36px;
    background-color: #ff4655;
    border: 1px solid #ff7f8a;
    color: #ffffff;
    font-size: 10px;
    font-weight: 700;
}
QPushButton#primaryButton:hover {
    background-color: #f33f4f;
    border-color: #ffffff;
}
QPushButton#primaryButton:disabled {
    color: #6f7278;
    background-color: #2a1a1d;
    border-color: #3a2428;
}
QPushButton#cancelButton {
    min-height: 36px;
    min-width: 102px;
    background-color: transparent;
    color: #d8dade;
}
QPushButton#cancelButton:disabled {
    color: #5f646d;
    background-color: #14171b;
    border-color: #292f37;
}
QPushButton#secondaryButton {
    min-height: 27px;
    padding: 0 12px;
    background-color: #1d2127;
}
QPushButton#recordButton {
    min-height: 27px;
    min-width: 72px;
    background-color: transparent;
    border-color: #414852;
    color: #eceef1;
    font-weight: 600;
}
QPushButton#recordButton:hover {
    background-color: #22262d;
    border-color: #ff4655;
    color: #ffffff;
}
QPushButton#recordButton[recording="true"] {
    background-color: #ff4655;
    border-color: #ff8a94;
    color: #ffffff;
}
QPushButton#recordButton:disabled {
    color: #5f646d;
    background-color: #14171b;
    border-color: #292f37;
}
QPushButton#discardRecordButton {
    min-height: 27px;
    min-width: 72px;
    background-color: #181b20;
    border-color: #565d68;
    color: #c8cbd0;
}
QPushButton#discardRecordButton:hover {
    border-color: #ff4655;
    color: #ffffff;
}
QPushButton#browseButton {
    min-height: 30px;
    padding: 0;
}
QPushButton#removeAudioButton {
    min-width: 25px;
    max-width: 25px;
    min-height: 25px;
    max-height: 25px;
    padding: 0;
    border-radius: 12px;
    background-color: transparent;
    border: 1px solid #454c57;
    color: #8f959e;
    font-size: 14px;
    font-weight: 600;
}
QPushButton#removeAudioButton:hover {
    background-color: #211a1d;
    border-color: #ff4655;
    color: #ffffff;
}
QPushButton#openFileButton, QPushButton#openFolderButton {
    min-height: 30px;
    background-color: #171a20;
    color: #e8eaed;
    font-weight: 600;
    border-color: #414852;
}
QPushButton#openFileButton:hover, QPushButton#openFolderButton:hover {
    background-color: #211a1d;
    border-color: #ff4655;
    color: #ffffff;
}
QPushButton#openFileButton:disabled, QPushButton#openFolderButton:disabled {
    color: #5f646d;
    background-color: #14171b;
    border-color: #292f37;
}
QComboBox, QLineEdit {
    min-height: 30px;
    background-color: #171a20;
    border: 1px solid #454c57;
    border-radius: 4px;
    padding: 0 8px;
    color: #eff0f2;
    selection-background-color: #ff4655;
}
QComboBox:disabled, QLineEdit:disabled {
    color: #5f646d;
    background-color: #14171b;
    border-color: #292f37;
}
QComboBox {
    padding-right: 28px;
}
QComboBox:focus, QLineEdit:focus {
    border-color: #454c57;
}
QComboBox:hover, QLineEdit:hover {
    border-color: #ff4655;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 27px;
    border: none;
    border-left: 1px solid #2d333b;
    background-color: #15191f;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}
QComboBox::down-arrow {
    image: none;
    width: 0px;
    height: 0px;
}
QComboBox QAbstractItemView {
    background-color: #171a20;
    border: 1px solid #454c57;
    selection-background-color: #ff4655;
    outline: 0;
    padding: 3px;
}
QProgressBar {
    min-height: 5px;
    max-height: 5px;
    border: none;
    border-radius: 2px;
    background-color: #2a2e35;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #ff4655;
    border-radius: 2px;
}
"""

