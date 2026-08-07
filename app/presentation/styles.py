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
QLabel#footerLabel {
    color: #767b84;
    font-size: 8px;
    font-weight: 500;
}
QFrame#audioInput {
    background-color: #171a20;
    border: 2px dashed #343a44;
    border-radius: 6px;
}
QFrame#audioInput[dragActive="true"] {
    background-color: #1b1e25;
    border: 2px dashed #ff4655;
}
QFrame#fileCard {
    background-color: #171a20;
    border: 2px dashed #343a44;
    border-radius: 6px;
}
QFrame#progressFrame {
    background-color: transparent;
    border: none;
}
QFrame#footerDivider {
    background-color: transparent;
    border: none;
    border-top: 1px dashed #2a2f38;
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
    border: 2px dashed #353b44;
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
    border-color: #262b33;
}
QPushButton#primaryButton {
    min-height: 36px;
    background-color: #ff4655;
    border: 2px dashed #ff98a1;
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
    min-width: 102px;
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
    border-color: #353b44;
}
QPushButton#openFileButton:hover, QPushButton#openFolderButton:hover {
    background-color: #211a1d;
    border-color: #ff4655;
    color: #ffffff;
}
QComboBox, QLineEdit {
    min-height: 30px;
    background-color: #171a20;
    border: 2px dashed #353b44;
    border-radius: 4px;
    padding: 0 8px;
    color: #eff0f2;
    selection-background-color: #ff4655;
}
QComboBox {
    padding-right: 26px;
}
QComboBox:hover, QLineEdit:hover {
    border-color: #5a606a;
}
QComboBox:focus, QLineEdit:focus {
    border-color: #ff4655;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 26px;
    border: none;
    border-left: 2px dashed #2c3139;
    background-color: #14181e;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}
QComboBox::down-arrow {
    image: none;
    width: 0px;
    height: 0px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #cfd3da;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #171a20;
    border: 2px dashed #353b44;
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
