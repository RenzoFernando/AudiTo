from __future__ import annotations

APP_STYLE = """
QMainWindow, QWidget {
    background-color: #0f1115;
    color: #f0f1f3;
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
    color: #ff4655;
}
QLabel#progressStatusLabel {
    color: #d8dade;
    font-size: 10px;
}
QLabel#progressStatusLabel[state="completed"] {
    color: #ff6572;
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
QFrame#audioInput {
    background-color: #171a20;
    border: 1px dotted #3a3f48;
    border-radius: 4px;
}
QFrame#audioInput[dragActive="true"] {
    background-color: #1b1e25;
    border: 1px dotted #ff4655;
}
QFrame#fileCard {
    background-color: #171a20;
    border: 1px dotted #343943;
    border-radius: 4px;
}
QFrame#progressFrame {
    background-color: transparent;
    border: none;
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
    border-radius: 3px;
    border: 1px dotted #3a4049;
    background-color: #1a1e24;
    color: #eceef1;
    font-size: 10px;
}
QPushButton:hover {
    background-color: #22262d;
    border-color: #ff4655;
}
QPushButton:pressed {
    background-color: #171a20;
}
QPushButton:disabled {
    color: #5f646d;
    background-color: #14171b;
    border-color: #292d34;
}
QPushButton#primaryButton {
    min-height: 36px;
    background-color: #ff4655;
    border: 1px dotted #ff8a94;
    color: #ffffff;
    font-size: 10px;
    font-weight: 700;
}
QPushButton#primaryButton:hover {
    background-color: #f33f4f;
    border-color: #ffffff;
}
QPushButton#cancelButton {
    min-height: 36px;
    min-width: 86px;
    background-color: transparent;
    color: #d8dade;
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
    border-color: #ff4655;
    color: #ff6572;
    font-weight: 600;
}
QPushButton#recordButton[recording="true"] {
    background-color: #ff4655;
    border-color: #ff8a94;
    color: #ffffff;
}
QPushButton#browseButton {
    min-height: 30px;
    padding: 0;
}
QPushButton#openFileButton, QPushButton#openFolderButton {
    min-height: 30px;
    background-color: #171a20;
    color: #e8eaed;
    font-weight: 600;
}
QPushButton#openFileButton {
    border-color: #ff4655;
}
QPushButton#openFolderButton {
    border-color: #444a54;
}
QPushButton#openFileButton:hover, QPushButton#openFolderButton:hover {
    background-color: #211a1d;
    border-color: #ff4655;
    color: #ffffff;
}
QComboBox, QLineEdit {
    min-height: 30px;
    background-color: #171a20;
    border: 1px dotted #3a4049;
    border-radius: 3px;
    padding: 0 8px;
    color: #eff0f2;
    selection-background-color: #ff4655;
}
QComboBox:hover, QLineEdit:hover {
    border-color: #5a606a;
}
QComboBox:focus, QLineEdit:focus {
    border-color: #ff4655;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #171a20;
    border: 1px dotted #3a4049;
    selection-background-color: #ff4655;
    outline: 0;
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
