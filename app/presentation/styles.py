from __future__ import annotations

APP_STYLE = """
QMainWindow, QWidget {
    background-color: #17191c;
    color: #eceef0;
    font-family: "Segoe UI";
    font-size: 11px;
}
QLabel {
    background-color: transparent;
    border: none;
}
QLabel#brandLabel {
    font-size: 20px;
    font-weight: 700;
    color: #d84b4b;
}
QLabel#sectionLabel {
    color: #aeb3b9;
    font-size: 10px;
    font-weight: 600;
}
QLabel#dropTitle {
    color: #f3f4f5;
    font-size: 14px;
    font-weight: 600;
}
QLabel#mutedLabel {
    color: #858c94;
    font-size: 10px;
}
QLabel#fileNameLabel {
    color: #f0f1f2;
    font-size: 11px;
    font-weight: 600;
}
QLabel#fileMetaLabel {
    color: #89919a;
    font-size: 10px;
}
QLabel#progressStatusLabel {
    color: #cfd3d7;
    font-size: 10px;
}
QLabel#etaLabel {
    color: #9ca3aa;
    font-size: 10px;
}
QLabel#localLabel {
    color: #84b99a;
    font-size: 10px;
}
QFrame#dropZone {
    background-color: #1d2024;
    border: 1px dashed #464c53;
    border-radius: 9px;
}
QFrame#dropZone[dragActive="true"] {
    background-color: #22262b;
    border: 1px solid #d84b4b;
}
QFrame#fileCard {
    background-color: #1d2024;
    border: 1px solid #2c3137;
    border-radius: 8px;
}
QFrame#progressFrame {
    background-color: transparent;
    border: none;
}
QFrame#footerFrame {
    background-color: transparent;
    border-top: 1px solid #272b30;
}
QPushButton {
    min-height: 31px;
    padding: 0 11px;
    border-radius: 7px;
    border: 1px solid #343a40;
    background-color: #23272c;
    color: #e8eaec;
    font-size: 11px;
}
QPushButton:hover {
    background-color: #2a2f35;
    border-color: #41484f;
}
QPushButton:pressed {
    background-color: #202429;
}
QPushButton:disabled {
    color: #666d74;
    background-color: #1d2024;
    border-color: #292e33;
}
QPushButton#primaryButton {
    min-height: 37px;
    background-color: #cf4747;
    border-color: #cf4747;
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
}
QPushButton#primaryButton:hover {
    background-color: #da5050;
    border-color: #da5050;
}
QPushButton#cancelButton {
    min-height: 37px;
    background-color: transparent;
    color: #cfd2d5;
}
QPushButton#secondaryButton {
    min-height: 29px;
    padding: 0 12px;
    background-color: #252a2f;
}
QPushButton#browseButton {
    min-height: 31px;
    padding: 0;
}
QComboBox, QLineEdit {
    min-height: 31px;
    background-color: #1d2024;
    border: 1px solid #343a40;
    border-radius: 7px;
    padding: 0 9px;
    color: #e8eaec;
    selection-background-color: #cf4747;
}
QComboBox:hover, QLineEdit:hover {
    border-color: #444b52;
}
QComboBox:focus, QLineEdit:focus {
    border-color: #b84646;
}
QComboBox::drop-down {
    border: none;
    width: 26px;
}
QComboBox QAbstractItemView {
    background-color: #1d2024;
    border: 1px solid #343a40;
    selection-background-color: #cf4747;
    outline: 0;
}
QProgressBar {
    min-height: 6px;
    max-height: 6px;
    border: none;
    border-radius: 3px;
    background-color: #2a2f34;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #cf4747;
    border-radius: 3px;
}
"""
