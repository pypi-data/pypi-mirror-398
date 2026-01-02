
import sys
import os
import json
import threading
import hashlib
import logging
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QDialog, 
                               QFormLayout, QLineEdit, QComboBox, QMessageBox, 
                               QFrame, QSizePolicy, QGraphicsDropShadowEffect,
                               QMenuBar, QMenu, QTabWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QCheckBox, QScrollArea, QDialogButtonBox,
                               QAbstractItemView, QFileDialog, QListWidget, QListWidgetItem, QInputDialog, 
                               QTextEdit, QGroupBox, QGridLayout)
from . import licensing
from . import paths
import requests


from PySide6.QtCore import Qt, QTimer, Signal, QObject, QThread, QMetaObject
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QAction, QIcon, QTextCursor

# --- Internationalization ---

class Translator:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Translator, cls).__new__(cls)
            cls._instance.translations = {}
            cls._instance.current_lang = "en"
        return cls._instance
    
    def load_language(self, lang_code):
        self.current_lang = lang_code
        # Look in package 'locales' directory
        path = os.path.join(os.path.dirname(__file__), 'locales', f'{lang_code}.json')
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                return True
            except Exception as e:
                print(f"Error loading locale {lang_code}: {e}")
        return False

    def get(self, key, default=None):
        return self.translations.get(key, default or key)

# Global instance
_translator = Translator()

def T(key, default=None):
    return _translator.get(key, default)

# --- Utils ---
# Import the server module
import opscalesrv
from opscalesrv import load_opscalesrv_config, anpr

# --- Styling ---

STYLESHEET = """
* {
    color: #E0E0E0;
    selection-background-color: #BB86FC;
    selection-color: #000000;
}
QMainWindow, QDialog, QWidget {
    background-color: #121212;
}
QMenuBar {
    background-color: #121212;
    border-bottom: 1px solid #333333;
}
QMenuBar::item:selected {
    background-color: #333333;
}
QMenu {
    background-color: #1E1E1E;
    border: 1px solid #333333;
}
QMenu::item:selected {
    background-color: #BB86FC;
    color: #000000;
}
QLabel {
    background-color: transparent;
    border: none;
}
QPushButton {
    background-color: #2D2D2D;
    border: 1px solid #3E3E3E;
    border-radius: 4px;
    padding: 6px 12px;
}
QPushButton:hover {
    background-color: #3D3D3D;
    border: 1px solid #505050;
}
QPushButton:pressed {
    background-color: #505050;
}
QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {
    background-color: #2D2D2D;
    border: 1px solid #3E3E3E;
    border-radius: 4px;
    padding: 6px;
    color: #FFFFFF;
}
QComboBox::drop-down {
    border: none;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #E0E0E0;
    margin-right: 5px;
}
QComboBox QAbstractItemView {
    background-color: #1E1E1E;
    border: 1px solid #333333;
    selection-background-color: #BB86FC;
    selection-color: #000000;
}
QTableWidget, QTableView {
    background-color: #1E1E1E;
    gridline-color: #333333;
    border: 1px solid #333333;
}
QTableWidget::item, QTableView::item {
    background-color: #1E1E1E;
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: #BB86FC;
    color: #000000;
}
QHeaderView, QHeaderView::section {
    background-color: #2D2D2D;
    color: #FFFFFF;
    padding: 4px;
    border: none;
    border-right: 1px solid #333333;
    border-bottom: 1px solid #333333;
}
QCheckBox {
    spacing: 5px;
    background-color: transparent;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #3E3E3E;
    background-color: #2D2D2D;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    background-color: #BB86FC;
    border-color: #BB86FC;
}
QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {
    background-color: #121212;
    border: none;
}
QScrollBar:vertical {
    border: none;
    background: #121212;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #3E3E3E;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QTabWidget::pane {
    border: 1px solid #333333;
    background-color: #121212;
}
QTabBar::tab {
    background-color: #1E1E1E;
    border: 1px solid #333333;
    padding: 8px 12px;
    color: #B0B0B0;
}
QTabBar::tab:selected {
    background-color: #BB86FC;
    color: #000000;
}
ModernFrame {
    background-color: #1E1E1E;
}
"""

class SignalManager(QObject):
    request_received = Signal(dict)
    request_started = Signal(dict)

# Global signal manager
signal_manager = SignalManager()

def server_callback(data):
    signal_manager.request_received.emit(data)


def server_start_callback(data_or_ip, path=None):
    if isinstance(data_or_ip, dict):
        signal_manager.request_started.emit(data_or_ip)
    else:
        signal_manager.request_started.emit({'client_ip': data_or_ip, 'path': path})




# --- Configuration Manager ---

class ConfigManager:
    @staticmethod
    def get_default_config():
        """Return default configuration without password"""
        return {
            "allowed_hosts": [
                {
                    "ip": "127.0.0.1",
                    "ports": [7373, 7374, 7375, 7376, 7377, 7378, 7379, 7380, 7381, 8080],
                    "description": "Localhost access"
                },
                {
                    "ip": "192.168.1.53",
                    "ports": [7373, 7374, 7375, 7376, 7377, 7378, 7379, 7380, 7381, 8080],
                    "description": "Local network access"
                },
                {
                    "ip": "localhost",
                    "ports": [7373, 7374, 7375, 7376, 7377, 7378, 7379, 7380, 7381, 8080],
                    "description": "Localhost hostname access"
                }
            ],
            "serial": {
                "port": "/dev/ttyUSB0",
                "baudrate": 9600,
                "bytesize": 8,
                "parity": "N",
                "stopbits": 1,
                "timeout": 1,
                "xonxoff": False,
                "rtscts": False,
                "dsrdtr": False,
                "write_timeout": None,
                "inter_byte_timeout": None,
                "exclusive": None,
                "description": "Serial port configuration for data reading - all pyserial parameters supported"
            },
            "settings": {
                "log_file": "requests.log",
                "deny_unknown_hosts": True,
                "log_all_requests": True,
                "encode": "utf-8",
                "language": "en",
                "name": "OpScale Server",
                "port": 7373


            },
            "query": {
                "timeout": 10,
                "parallel_read": True,
                "force_read": False,
                "cache_duration": 3.0,
                "retry_count": 1,
                "entrance": {
                    "server": "10.10.145.36",
                    "port": 80,
                    "URL": "/ISAPI/Event/notification/alertStream",
                    "username": "admin",
                    "password": "",
                    "plate": "licensePlate"
                },
                "exit": {
                    "server": "10.10.145.36",
                    "port": 80,
                    "URL": "/ISAPI/Event/notification/alertStream",
                    "username": "admin",
                    "password": "",
                    "plate": "licensePlate"
                }
            },
            "listener": {
                "port": 7382,
                "plate_tag": "licensePlate",
                "tolerance_minutes": 5,
                "description": "Passive HTTP listener for ANPR notifications"
            }
        }

    
    @staticmethod
    def load_config():
        config_path = paths.get_config_path()
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        # If config doesn't exist, create it with defaults
        default_config = ConfigManager.get_default_config()
        ConfigManager.save_config(default_config)
        return default_config

    @staticmethod
    def save_config(config):
        config_path = paths.get_config_path()
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    @staticmethod
    def reset_to_default():
        """Reset configuration to default values"""
        default_config = ConfigManager.get_default_config()
        ConfigManager.save_config(default_config)
        return default_config

# --- Custom Widgets ---

class TrafficLight(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)
        self.state = "IDLE" 
        self.color = QColor("#FFC107")  # Initial state (Yellow)
        
        # Glow effect
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(30)
        self.glow.setColor(self.color)
        self.glow.setOffset(0, 0)
        self.setGraphicsEffect(self.glow)

    def set_state(self, status):
        """
        Status can be:
        - True (bool): Treated as 'OK'
        - False (bool): Treated as 'FAIL'
        - 'OK' (str): Green
        - 'FAIL' (str): Red
        - 'IDLE' (str): Yellow
        - 'PROCESSING' (str): Pulsing Red
        """
        if hasattr(self, 'pulse_timer'):
            self.pulse_timer.stop()

        if isinstance(status, bool):
            self.state = 'OK' if status else 'FAIL'
        else:
            self.state = str(status).upper()

        if self.state == 'OK':
            self.color = QColor("#00E676")  # Green
        elif self.state == 'FAIL' or self.state == 'ERROR':
            self.color = QColor("#FF5252")  # Red
        elif self.state == 'PROCESSING':
            self.color = QColor("#FF5252")  # Red for processing
            if not hasattr(self, 'pulse_timer'):
                self.pulse_timer = QTimer(self)
                self.pulse_timer.timeout.connect(self._pulse_tick)
            self.pulse_val = 0
            self.pulse_dir = 1
            # Start timer with shorter interval for more visible pulsing
            self.pulse_timer.start(50)
            # Force immediate update and repaint
            self.update()
            self.repaint()
            # Log to verify timer started
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"TrafficLight: PROCESSING state set, timer started: {self.pulse_timer.isActive()}")
        else:
            self.color = QColor("#FFC107")  # Yellow (IDLE)
        
        self.glow.setColor(self.color)
        self.glow.setBlurRadius(30)
        self.update()

    def _pulse_tick(self):
        """Timer callback for pulsing animation"""
        self.pulse_val += self.pulse_dir * 5
        if self.pulse_val > 50 or self.pulse_val < 0:
            self.pulse_dir *= -1
        self.glow.setBlurRadius(20 + self.pulse_val)
        # Make the color itself pulse too
        p_color = QColor(self.color)
        alpha = 150 + self.pulse_val * 2
        p_color.setAlpha(min(255, max(0, int(alpha))))
        self.glow.setColor(p_color)
        self.update()
        # Log first few ticks to verify it's working
        if not hasattr(self, '_pulse_tick_count'):
            self._pulse_tick_count = 0
        self._pulse_tick_count += 1
        if self._pulse_tick_count <= 3:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"TrafficLight _pulse_tick called (count: {self._pulse_tick_count}, pulse_val: {self.pulse_val})")





    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.setBrush(QBrush(self.color.darker(180)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(10, 10, 60, 60)
        
        # Draw active circle - Always draw roughly same size but color changes
        # For 'dimmed' look we could use darker color, but user wants 'Yellow', 'Red', 'Green'
        # Let's make it always 'active' looking so the color is visible.
        painter.setBrush(QBrush(self.color))
        painter.drawEllipse(15, 15, 50, 50)

class ModernFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            ModernFrame {
                background-color: #1E1E1E;
                border-radius: 12px;
                border: 1px solid #333333;
            }
        """)

# --- Settings Dialogs ---

class SerialSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T("title_serial_settings"))
        self.resize(400, 500)
        layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.form_layout = QFormLayout(content)
        
        self.inputs = {}
        self.config = ConfigManager.load_config().get('serial', {})
        
        # Define fields based on JSON structure
        self.add_field("port", T("lbl_port"), str)

        self.add_field("baudrate", T("lbl_baudrate"), int, options=["9600", "19200", "38400", "57600", "115200"])
        self.add_field("bytesize", T("lbl_bytesize"), int, options=["5", "6", "7", "8"])
        self.add_field("parity", T("lbl_parity"), str, options=["N", "E", "O", "M", "S"])
        self.add_field("stopbits", T("lbl_stopbits"), float, options=["1", "1.5", "2"])
        self.add_field("timeout", T("lbl_timeout_s"), float)
        self.add_field("xonxoff", T("lbl_xonxoff"), bool)
        self.add_field("rtscts", T("lbl_rtscts"), bool)
        self.add_field("dsrdtr", T("lbl_dsrdtr"), bool)
        self.add_field("write_timeout", T("lbl_write_timeout"), float, nullable=True)
        self.add_field("inter_byte_timeout", T("lbl_inter_byte_timeout"), float, nullable=True)
        self.add_field("exclusive", T("lbl_exclusive_access"), bool, nullable=True)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.save_data)
        btns.rejected.connect(self.reject)

        btns.button(QDialogButtonBox.Save).setText(T("btn_save"))
        btns.button(QDialogButtonBox.Cancel).setText(T("btn_cancel"))
        
        layout.addWidget(btns)

    def add_field(self, key, label, type_, options=None, nullable=False):
        val = self.config.get(key)
        
        if type_ == bool:
            widget = QCheckBox()
            widget.setChecked(bool(val))
            self.inputs[key] = (widget, type_)
        elif options:
            widget = QComboBox()
            widget.addItems(options)
            widget.setCurrentText(str(val) if val is not None else options[0])
            self.inputs[key] = (widget, type_)
        else:
            widget = QLineEdit()
            if val is not None:
                widget.setText(str(val))
            if nullable:
                widget.setPlaceholderText("None")
            self.inputs[key] = (widget, type_)
            
        self.form_layout.addRow(label, widget)

    def save_data(self):
        full_config = ConfigManager.load_config()
        new_serial_config = full_config.get('serial', {})
        
        for key, (widget, type_) in self.inputs.items():
            if type_ == bool:
                new_serial_config[key] = widget.isChecked()
            else:
                text = widget.currentText() if isinstance(widget, QComboBox) else widget.text()
                if not text and (isinstance(widget, QLineEdit) or widget.placeholderText() == "None"):
                    new_serial_config[key] = None
                else:
                    try:
                        if type_ == int:
                            new_serial_config[key] = int(text)
                        elif type_ == float:
                            new_serial_config[key] = float(text)
                        else:
                            new_serial_config[key] = text
                    except ValueError:
                        QMessageBox.warning(self, T("msg_invalid_input"), f"{T('msg_invalid_value_for')} {key}")
                        return

        full_config['serial'] = new_serial_config
        ConfigManager.save_config(full_config)
        self.accept()

class AllowedHostsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T("title_allowed_hosts"))
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([T("hdr_ip_address"), T("hdr_ports"), T("hdr_description")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton(T("btn_add_host"))
        add_btn.clicked.connect(self.add_row)
        remove_btn = QPushButton(T("btn_remove_selected"))
        remove_btn.clicked.connect(self.remove_row)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)
        
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.save_data)
        btns.rejected.connect(self.reject)

        btns.button(QDialogButtonBox.Save).setText(T("btn_save"))
        btns.button(QDialogButtonBox.Cancel).setText(T("btn_cancel"))
        
        layout.addWidget(btns)
        
        self.load_data()

    def load_data(self):
        hosts = ConfigManager.load_config().get('allowed_hosts', [])
        self.table.setRowCount(len(hosts))
        for i, host in enumerate(hosts):
            self.table.setItem(i, 0, QTableWidgetItem(host.get('ip', '')))
            ports = ",".join(map(str, host.get('ports', [])))
            self.table.setItem(i, 1, QTableWidgetItem(ports))
            self.table.setItem(i, 2, QTableWidgetItem(host.get('description', '')))

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

    def remove_row(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)

    def save_data(self):
        hosts = []
        for i in range(self.table.rowCount()):
            ip = self.table.item(i, 0).text() if self.table.item(i, 0) else ""
            ports_str = self.table.item(i, 1).text() if self.table.item(i, 1) else ""
            desc = self.table.item(i, 2).text() if self.table.item(i, 2) else ""
            
            if not ip: continue
            
            try:
                ports = [int(p.strip()) for p in ports_str.split(',') if p.strip()]
            except ValueError:
                QMessageBox.warning(self, T("msg_invalid_input"), f"{T('msg_invalid_ports_format')} {ip}")
                return
                
            hosts.append({
                "ip": ip,
                "ports": ports,
                "description": desc
            })
            
        full_config = ConfigManager.load_config()
        full_config['allowed_hosts'] = hosts
        ConfigManager.save_config(full_config)
        self.accept()

class GeneralSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T("title_general"))
        self.resize(400, 350)
        layout = QVBoxLayout(self)
        
        self.form_layout = QFormLayout()
        
        self.inputs = {}
        self.config = ConfigManager.load_config().get('settings', {})
        full_config = ConfigManager.load_config()
        
        # Server Name
        self.add_field("name", T("lbl_server_name", "Server Name"), str)
        
        # Server URL
        self.add_field("server_url", T("lbl_server_url", "Server URL"), str)
        
        # Language Selection
        lang_val = self.config.get("language", "en")
        self.add_field("language", T("lbl_language"), list, options=["en", "tr", "de", "fr", "ru", "ja", "ko"], current=lang_val)
        
        # Serial Enabled (from settings.serial)
        self.serial_enabled_cb = QCheckBox(T("lbl_serial_enabled", "Serial Enabled"))
        self.serial_enabled_cb.setChecked(self.config.get('serial', True))
        self.form_layout.addRow(T("lbl_serial_enabled", "Serial Enabled"), self.serial_enabled_cb)
        
        # ANPR(ISAPI) Mode Selection (from settings.isapi)
        self.anpr_isapi_cb = QComboBox()
        self.anpr_isapi_cb.addItems(["disabled", "query", "listen"])
        anpr_isapi_mode = self.config.get('isapi', 'disabled')
        if anpr_isapi_mode in ["query", "listen", "disabled"]:
            self.anpr_isapi_cb.setCurrentText(anpr_isapi_mode)
        else:
            self.anpr_isapi_cb.setCurrentText("disabled")
        self.form_layout.addRow(T("lbl_anpr_isapi", "ANPR(ISAPI)"), self.anpr_isapi_cb)
        
        self.add_field("port", T("lbl_port"), int)
        self.add_field("log_file", T("lbl_log_file"), str)
        self.add_field("encode", T("lbl_encoding"), str)
        self.add_field("deny_unknown_hosts", T("lbl_deny_hosts"), bool)
        self.add_field("log_all_requests", T("lbl_log_all"), bool)
        
        layout.addLayout(self.form_layout)
        
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.save_data)
        btns.rejected.connect(self.reject)
        
        # Translate buttons
        btns.button(QDialogButtonBox.Save).setText(T("btn_save"))
        btns.button(QDialogButtonBox.Cancel).setText(T("btn_cancel"))
        
        layout.addWidget(btns)

    def add_field(self, key, label, type_, options=None, current=None):
        val = self.config.get(key)
        if type_ == bool:
            widget = QCheckBox()
            widget.setChecked(bool(val))
        elif type_ == list:
            widget = QComboBox()
            if options:
                widget.addItems(options)
                if current and current in options:
                    widget.setCurrentText(current)
                elif val and str(val) in options: # Fallback for existing config
                    widget.setCurrentText(str(val))
        else:
            widget = QLineEdit()
            if val is not None: # Ensure 0 or False are not treated as empty
                widget.setText(str(val))
            
        self.inputs[key] = (widget, type_)
        self.form_layout.addRow(label, widget)

    def save_data(self):
        full_config = ConfigManager.load_config()
        new_settings = full_config.get('settings', {})
        
        for key, (widget, type_) in self.inputs.items():
            if type_ == bool:
                new_settings[key] = widget.isChecked()
            elif type_ == list:
                new_settings[key] = widget.currentText()
            else:
                text = widget.text()
                try:
                    if type_ == int:
                        new_settings[key] = int(text)
                    elif type_ == float:
                        new_settings[key] = float(text)
                    else:
                        new_settings[key] = text
                except ValueError:
                    QMessageBox.warning(self, T("msg_invalid_input"), f"{T('msg_invalid_value_for')} {key}")
                    return
        
        # Save serial enabled to settings.serial
        new_settings['serial'] = self.serial_enabled_cb.isChecked()
        
        # Save ANPR(ISAPI) mode to settings.isapi
        new_settings['isapi'] = self.anpr_isapi_cb.currentText()
                
        full_config['settings'] = new_settings
        ConfigManager.save_config(full_config)
        self.accept()

class CheckPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T("title_auth_required"))
        self.resize(300, 150)
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel(T("lbl_enter_password")))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_edit)
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        btns.button(QDialogButtonBox.Ok).setText(T("btn_ok"))
        btns.button(QDialogButtonBox.Cancel).setText(T("btn_cancel"))
        
        layout.addWidget(btns)
        
    def get_password(self):
        return self.password_edit.text()

class SetPasswordDialog(QDialog):
    def __init__(self, has_current_password=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T("title_set_password"))
        self.resize(300, 200)
        self.has_current = has_current_password
        
        layout = QFormLayout(self)
        
        self.current_pwd = QLineEdit()
        self.current_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.confirm_pwd = QLineEdit()
        self.confirm_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        
        if has_current_password:
            layout.addRow(T("lbl_current_password"), self.current_pwd)
            
        layout.addRow(T("lbl_new_password"), self.new_pwd)
        layout.addRow(T("lbl_confirm_password"), self.confirm_pwd)
        
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.validate_and_save)
        btns.rejected.connect(self.reject)

        btns.button(QDialogButtonBox.Save).setText(T("btn_save"))
        btns.button(QDialogButtonBox.Cancel).setText(T("btn_cancel"))
        
        layout.addWidget(btns)
        
    def validate_and_save(self):
        if self.new_pwd.text() != self.confirm_pwd.text():
            QMessageBox.warning(self, T("msg_error"), T("msg_passwords_no_match"))
            return
            
        self.accept()
        
    def get_data(self):
        return self.current_pwd.text(), self.new_pwd.text()

class ANPRSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T("title_anpr"))
        self.resize(700, 600)
        
        self.config = ConfigManager.load_config().get('query', {})  # Changed from 'anpr' to 'query'
        self.working_config = dict(self.config)
        
        # Migrate old format (entrance/exit) to new format (cameras list)
        if 'cameras' not in self.working_config:
            self.working_config['cameras'] = []
            # Migrate entrance if exists
            if 'entrance' in self.working_config:
                entrance_cam = dict(self.working_config['entrance'])
                entrance_cam['name'] = 'Entrance'
                self.working_config['cameras'].append(entrance_cam)
            # Migrate exit if exists
            if 'exit' in self.working_config:
                exit_cam = dict(self.working_config['exit'])
                exit_cam['name'] = 'Exit'
                self.working_config['cameras'].append(exit_cam)
        
        layout = QVBoxLayout(self)
        
        # Advanced Global Settings
        adv_group = QGroupBox(T("lbl_advanced_settings", "Advanced Settings"))
        adv_layout = QGridLayout(adv_group)
        
        self.parallel_cb = QCheckBox(T("lbl_parallel_read", "Parallel Read"))
        self.parallel_cb.setChecked(self.working_config.get('parallel_read', True))
        self.parallel_cb.setToolTip(T("tip_parallel_read", "Read serial and camera concurrently"))
        
        self.force_read_cb = QCheckBox(T("lbl_force_read", "Force Read"))
        self.force_read_cb.setChecked(self.working_config.get('force_read', False))
        self.force_read_cb.setToolTip(T("tip_force_read", "Read plate even if serial fails"))
        
        self.cache_edit = QLineEdit(str(self.working_config.get('cache_duration', 3.0)))
        self.retry_edit = QLineEdit(str(self.working_config.get('retry_count', 1)))
        
        adv_layout.addWidget(self.parallel_cb, 0, 0)
        adv_layout.addWidget(self.force_read_cb, 0, 1)
        adv_layout.addWidget(QLabel(T("lbl_cache_duration", "Cache (s)")), 1, 0)
        adv_layout.addWidget(self.cache_edit, 1, 1)
        adv_layout.addWidget(QLabel(T("lbl_retry_count", "Retry Count")), 2, 0)
        adv_layout.addWidget(self.retry_edit, 2, 1)
        
        layout.addWidget(adv_group)
        
        layout.addSpacing(15)
        
        # Camera List Section
        cam_group = QGroupBox(T("lbl_cameras", "Cameras"))
        cam_layout = QVBoxLayout(cam_group)
        
        # Camera List Widget
        list_layout = QHBoxLayout()
        self.camera_list = QListWidget()
        self.camera_list.itemSelectionChanged.connect(self.on_camera_selected)
        self.camera_list.itemDoubleClicked.connect(self.edit_camera)
        list_layout.addWidget(self.camera_list)
        
        # Camera List Buttons
        btn_layout = QVBoxLayout()
        self.add_btn = QPushButton(T("btn_add_camera", "Add Camera"))
        self.add_btn.clicked.connect(self.add_camera)
        self.edit_btn = QPushButton(T("btn_edit_camera", "Edit"))
        self.edit_btn.clicked.connect(self.edit_camera)
        self.delete_btn = QPushButton(T("btn_delete_camera", "Delete"))
        self.delete_btn.clicked.connect(self.delete_camera)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        list_layout.addLayout(btn_layout)
        
        cam_layout.addLayout(list_layout)
        layout.addWidget(cam_group)
        
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.save_data)
        btns.rejected.connect(self.reject)
        
        btns.button(QDialogButtonBox.Save).setText(T("btn_save"))
        btns.button(QDialogButtonBox.Cancel).setText(T("btn_cancel"))
        
        layout.addWidget(btns)
        
        # Populate camera list
        self.refresh_camera_list()

    def refresh_camera_list(self):
        """Refresh the camera list widget"""
        self.camera_list.clear()
        cameras = self.working_config.get('cameras', [])
        for i, cam in enumerate(cameras):
            name = cam.get('name', f'Camera {i+1}')
            enabled = "✓" if cam.get('enabled', True) else "✗"
            item_text = f"{enabled} {name}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, i)  # Store index
            self.camera_list.addItem(item)
    
    def on_camera_selected(self):
        """Handle camera selection"""
        current = self.camera_list.currentItem()
        self.edit_btn.setEnabled(current is not None)
        self.delete_btn.setEnabled(current is not None)
    
    def add_camera(self):
        """Add a new camera"""
        dialog = CameraEditDialog(self, None)
        if dialog.exec():
            camera_data = dialog.get_camera_data()
            if 'cameras' not in self.working_config:
                self.working_config['cameras'] = []
            self.working_config['cameras'].append(camera_data)
            self.refresh_camera_list()
    
    def edit_camera(self):
        """Edit selected camera"""
        current = self.camera_list.currentItem()
        if not current:
            return
        
        index = current.data(Qt.UserRole)
        cameras = self.working_config.get('cameras', [])
        if 0 <= index < len(cameras):
            dialog = CameraEditDialog(self, cameras[index])
            if dialog.exec():
                cameras[index] = dialog.get_camera_data()
                self.refresh_camera_list()
    
    def delete_camera(self):
        """Delete selected camera"""
        current = self.camera_list.currentItem()
        if not current:
            return
        
        reply = QMessageBox.question(
            self, 
            T("msg_confirm_delete", "Confirm Delete"),
            T("msg_confirm_delete_camera", "Are you sure you want to delete this camera?"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            index = current.data(Qt.UserRole)
            cameras = self.working_config.get('cameras', [])
            if 0 <= index < len(cameras):
                cameras.pop(index)
                self.refresh_camera_list()
    
    def save_data(self):
        """Save ANPR configuration"""
        self.working_config['parallel_read'] = self.parallel_cb.isChecked()
        self.working_config['force_read'] = self.force_read_cb.isChecked()
        
        try:
            self.working_config['cache_duration'] = float(self.cache_edit.text())
            self.working_config['retry_count'] = int(self.retry_edit.text())
        except:
            pass
        
        full_config = ConfigManager.load_config()
        full_config['query'] = self.working_config  # Changed from 'anpr' to 'query'
        ConfigManager.save_config(full_config)
        self.accept()


class CameraEditDialog(QDialog):
    """Dialog for adding/editing a camera"""
    def __init__(self, parent=None, camera_data=None):
        super().__init__(parent)
        self.setWindowTitle(T("title_edit_camera", "Edit Camera") if camera_data else T("title_add_camera", "Add Camera"))
        self.resize(450, 500)
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Camera Name
        self.name_edit = QLineEdit()
        form_layout.addRow(T("lbl_camera_name", "Camera Name"), self.name_edit)
        
        # Enabled Checkbox
        self.enabled_cb = QCheckBox(T("lbl_enable_camera", "Enable this camera"))
        form_layout.addRow("", self.enabled_cb)
        
        # Server IP
        self.server_edit = QLineEdit()
        form_layout.addRow(T("lbl_server_ip"), self.server_edit)
        
        # Port
        self.port_edit = QLineEdit()
        form_layout.addRow(T("lbl_cam_port"), self.port_edit)
        
        # URL
        self.url_edit = QLineEdit()
        form_layout.addRow(T("lbl_url"), self.url_edit)
        
        # Username
        self.username_edit = QLineEdit()
        form_layout.addRow(T("lbl_username"), self.username_edit)
        
        # Password
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow(T("lbl_password"), self.password_edit)
        
        # Plate Tag (XML tag to read from camera)
        self.plate_edit = QLineEdit()
        form_layout.addRow(T("lbl_plate"), self.plate_edit)
        
        # Response Tag (tag name in response JSON)
        self.response_tag_edit = QLineEdit()
        form_layout.addRow(T("lbl_response_tag", "Response Tag"), self.response_tag_edit)
        
        layout.addLayout(form_layout)
        
        # Load data if editing
        if camera_data:
            self.name_edit.setText(camera_data.get('name', ''))
            self.enabled_cb.setChecked(camera_data.get('enabled', True))
            self.server_edit.setText(str(camera_data.get('server', '')))
            self.port_edit.setText(str(camera_data.get('port', '')))
            self.url_edit.setText(str(camera_data.get('URL', '')))
            self.username_edit.setText(str(camera_data.get('username', '')))
            self.password_edit.setText(str(camera_data.get('password', '')))
            self.plate_edit.setText(str(camera_data.get('plate', 'licensePlate')))
            self.response_tag_edit.setText(str(camera_data.get('response_tag', '')))
        else:
            # Defaults for new camera
            self.enabled_cb.setChecked(True)
            self.server_edit.setText("10.10.145.36")
            self.port_edit.setText("80")
            self.url_edit.setText("/ISAPI/Event/notification/alertStream")
            self.username_edit.setText("admin")
            self.plate_edit.setText("licensePlate")
            self.response_tag_edit.setText("")
        
        # Test Button
        self.test_btn = QPushButton(T("btn_test"))
        self.test_btn.setStyleSheet("background-color: #3700B3; height: 35px;")
        self.test_btn.clicked.connect(self.test_camera_action)
        layout.addWidget(self.test_btn)
        
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.Ok).setText(T("btn_ok"))
        btns.button(QDialogButtonBox.Cancel).setText(T("btn_cancel"))
        layout.addWidget(btns)
    
    def get_camera_data(self):
        """Get camera data from form"""
        try:
            port = int(self.port_edit.text())
        except:
            port = 80
        
        return {
            'name': self.name_edit.text() or 'Camera',
            'enabled': self.enabled_cb.isChecked(),
            'server': self.server_edit.text(),
            'port': port,
            'URL': self.url_edit.text(),
            'username': self.username_edit.text(),
            'password': self.password_edit.text(),
            'plate': self.plate_edit.text() or 'licensePlate',
            'response_tag': self.response_tag_edit.text().strip()
        }
    
    def get_camera_settings_for_test(self):
        """Get camera settings from form for testing"""
        try:
            port = int(self.port_edit.text())
        except:
            port = 80
        
        return {
            'server': self.server_edit.text(),
            'port': port,
            'URL': self.url_edit.text(),
            'username': self.username_edit.text(),
            'password': self.password_edit.text(),
            'plate': self.plate_edit.text() or 'licensePlate',
            'timeout': 10
        }
    
    def test_camera_action(self):
        """Test camera connection"""
        # Get current settings from form
        cam_settings = self.get_camera_settings_for_test()
        
        # Validate required fields
        if not cam_settings['server']:
            QMessageBox.warning(self, T("msg_error"), "Server IP is required")
            return
        
        # Disable button and show status
        self.test_btn.setEnabled(False)
        self.test_btn.setText("Testing... (Window Responsive)")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        # Start background thread
        self.test_thread = CameraTestThread(cam_settings)
        self.test_thread.finished.connect(self.on_test_finished)
        self.test_thread.error.connect(self.on_test_error)
        self.test_thread.start()
    
    def on_test_error(self, err_msg):
        """Handle test error"""
        QApplication.restoreOverrideCursor()
        self.test_btn.setEnabled(True)
        self.test_btn.setText(T("btn_test"))
        QMessageBox.critical(self, T("msg_error"), f"Test failed: {err_msg}")
    
    def on_test_finished(self, result):
        """Handle test completion"""
        QApplication.restoreOverrideCursor()
        self.test_btn.setEnabled(True)
        self.test_btn.setText(T("btn_test"))
        
        xml_data, http_status, parsed_plate = result
        
        # Show in a dialog
        dlg = QDialog(self)
        dlg.setWindowTitle(T("title_anpr_test"))
        dlg.resize(800, 600)
        d_lay = QVBoxLayout(dlg)
        
        # INFO Header
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setStyleSheet("background-color: #2C2C2C; border-radius: 5px;")
        info_lay = QFormLayout(info_frame)
        
        status_lbl = QLabel(str(http_status))
        status_lbl.setStyleSheet(f"font-weight: bold; color: {'#4CAF50' if http_status == 200 else '#F44336'};")
        
        plate_lbl = QLabel(parsed_plate)
        plate_lbl.setStyleSheet("font-weight: bold; color: #BB86FC; font-size: 14px;")
        
        info_lay.addRow("HTTP Status Code:", status_lbl)
        info_lay.addRow("Parsed Plate (SAP):", plate_lbl)
        
        d_lay.addWidget(info_frame)
        d_lay.addWidget(QLabel("Raw Camera Response (XML):"))
        
        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText(xml_data)
        txt.setFont(QFont("Courier New", 10))
        d_lay.addWidget(txt)
        
        close_btn = QPushButton(T("btn_ok"))
        close_btn.setStyleSheet("height: 40px; font-weight: bold;")
        close_btn.clicked.connect(dlg.accept)
        d_lay.addWidget(close_btn)
        
        dlg.exec()

# --- Background Camera Test Thread ---

class CameraTestThread(QThread):
    finished = Signal(tuple)
    error = Signal(str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def run(self):
        try:
            result = anpr.test_camera(self.settings)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# --- Background Server Thread ---

class ServerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        
    def run(self):
        load_opscalesrv_config()
        config = ConfigManager.load_config()
        port = int(config.get('settings', {}).get('port', 7373))
        
        opscalesrv.ON_REQUEST_CALLBACK = server_callback
        opscalesrv.ON_START_CALLBACK = server_start_callback
        try:
            opscalesrv.start_server(port=port, host='0.0.0.0')
        except Exception as e:
            print(f"Server error: {e}")


class LicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T("title_licensing", "Licensing"))
        self.setFixedWidth(450)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        info_lbl = QLabel(T("msg_license_required", "A valid license is required to run this application."))
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("font-weight: bold; color: #BB86FC;")
        layout.addWidget(info_lbl)
        
        hid_layout = QVBoxLayout()
        hid_layout.addWidget(QLabel(T("lbl_hardware_id", "Hardware ID (HID):")))
        
        self.hid_edit = QLineEdit(licensing.get_machine_id())
        self.hid_edit.setReadOnly(True)
        self.hid_edit.setStyleSheet("background-color: #1E1E1E; font-family: monospace; font-size: 14px; border: 1px solid #BB86FC;")
        hid_layout.addWidget(self.hid_edit)
        
        copy_btn = QPushButton(T("btn_copy_hid", "Copy HID"))
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.hid_edit.text()))
        hid_layout.addWidget(copy_btn)
        layout.addLayout(hid_layout)
        
        layout.addSpacing(10)
        
        layout.addWidget(QLabel(T("lbl_enter_license", "Enter License Key:")))
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self.key_edit.setStyleSheet("font-size: 16px; height: 35px; color: #03DAC6; font-weight: bold; text-align: center;")
        layout.addWidget(self.key_edit)
        
        btn_layout = QHBoxLayout()
        self.activate_btn = QPushButton(T("btn_activate", "Activate"))
        self.activate_btn.setStyleSheet("background-color: #3700B3; height: 40px; font-weight: bold;")
        self.activate_btn.clicked.connect(self.check_activation)
        
        self.exit_btn = QPushButton(T("btn_exit", "Exit"))
        self.exit_btn.setStyleSheet("height: 40px;")
        self.exit_btn.clicked.connect(self.exit_application)
        
        btn_layout.addWidget(self.exit_btn)
        btn_layout.addWidget(self.activate_btn)
        layout.addLayout(btn_layout)

    def exit_application(self):
        """Exit button handler - closes dialog and terminates application"""
        self.reject()
        QApplication.instance().quit()
        sys.exit(0)

    def check_activation(self):
        key = self.key_edit.text().strip()
        if licensing.verify_license(key):
            # Save key to license.key file
            licensing.save_license(key)
            QMessageBox.information(self, T("msg_success"), T("msg_license_activated", "License activated successfully!"))
            self.accept()
        else:
            QMessageBox.critical(self, T("msg_error"), T("msg_invalid_license", "Invalid license key for this machine."))


class LogViewerDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T("title_logs"))
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Monospace", 10))
        layout.addWidget(self.text_edit)
        
        self.load_logs()
        
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton(T("btn_refresh", "Refresh")) # Fallback if key missing
        refresh_btn.clicked.connect(self.load_logs)
        close_btn = QPushButton(T("btn_close", "Close")) # Fallback
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
    def load_logs(self):
        config = ConfigManager.load_config()
        log_file = config.get('settings', {}).get('log_file', 'requests.log')
        
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Show last 1000 lines if too large? 
                    # For now show all, text edit handles reasonably sized files.
                    self.text_edit.setText(content)
                    self.text_edit.moveCursor(QTextCursor.End)
            except Exception as e:
                self.text_edit.setText(f"Error reading log file: {e}")
        else:
            self.text_edit.setText("Log file not found.")

# --- Main Window ---

class ANPRListenerSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T("title_anpr_listener", "ANPR Listener Settings"))
        self.resize(700, 600)
        
        self.config = ConfigManager.load_config().get('listener', {})  # Changed from 'anpr_listener' to 'listener'
        self.working_config = dict(self.config)
        
        # Migrate old format to new format (listeners list)
        if 'listeners' not in self.working_config:
            self.working_config['listeners'] = []
            # Migrate old single listener config if exists
            if self.working_config.get('enabled', False) or 'url' in self.working_config:
                listener = {
                    'name': 'Listener 1',
                    'enabled': self.working_config.get('enabled', False),
                    'url': self.working_config.get('url', '/anpr/notify'),
                    'plate_tag': self.working_config.get('plate_tag', 'licensePlate'),
                    'tolerance_minutes': self.working_config.get('tolerance_minutes', 5),
                    'picture_path': self.working_config.get('picture_path', os.path.join(os.path.expanduser("~"), "ANPR_Pictures"))
                }
                self.working_config['listeners'].append(listener)
        
        layout = QVBoxLayout(self)
        
        # Info
        info = QLabel(T("msg_anpr_listener_info", "Configure URL endpoints on the main server to receive ANPR notifications directly from cameras."))
        info.setWordWrap(True)
        info.setStyleSheet("color: #888888; font-style: italic;")
        layout.addWidget(info)
        layout.addSpacing(10)
        
        # Listener List Section
        listener_group = QGroupBox(T("lbl_listeners", "Listeners"))
        listener_layout = QVBoxLayout(listener_group)
        
        # Listener List Widget
        list_layout = QHBoxLayout()
        self.listener_list = QListWidget()
        self.listener_list.itemSelectionChanged.connect(self.on_listener_selected)
        self.listener_list.itemDoubleClicked.connect(self.edit_listener)
        list_layout.addWidget(self.listener_list)
        
        # Listener List Buttons
        btn_layout = QVBoxLayout()
        self.add_btn = QPushButton(T("btn_add_listener", "Add Listener"))
        self.add_btn.clicked.connect(self.add_listener)
        self.edit_btn = QPushButton(T("btn_edit_listener", "Edit"))
        self.edit_btn.clicked.connect(self.edit_listener)
        self.delete_btn = QPushButton(T("btn_delete_listener", "Delete"))
        self.delete_btn.clicked.connect(self.delete_listener)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        list_layout.addLayout(btn_layout)
        
        listener_layout.addLayout(list_layout)
        layout.addWidget(listener_group)
        
        # Tip
        tip_label = QLabel("ℹ️ " + T("tip_listener_url", "The server will accept POST requests on configured URL paths."))
        tip_label.setStyleSheet("color: #03DAC6; font-size: 11px;")
        layout.addWidget(tip_label)
        
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.save_data)
        btns.rejected.connect(self.reject)
        
        btns.button(QDialogButtonBox.Save).setText(T("btn_save"))
        btns.button(QDialogButtonBox.Cancel).setText(T("btn_cancel"))
        
        layout.addWidget(btns)
        
        # Populate listener list
        self.refresh_listener_list()



    def refresh_listener_list(self):
        """Refresh the listener list widget"""
        self.listener_list.clear()
        listeners = self.working_config.get('listeners', [])
        for i, listener in enumerate(listeners):
            name = listener.get('name', f'Listener {i+1}')
            enabled = "✓" if listener.get('enabled', True) else "✗"
            item_text = f"{enabled} {name}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, i)  # Store index
            self.listener_list.addItem(item)
    
    def on_listener_selected(self):
        """Handle listener selection"""
        current = self.listener_list.currentItem()
        self.edit_btn.setEnabled(current is not None)
        self.delete_btn.setEnabled(current is not None)
    
    def add_listener(self):
        """Add a new listener"""
        dialog = ListenerEditDialog(self, None)
        if dialog.exec():
            listener_data = dialog.get_listener_data()
            if 'listeners' not in self.working_config:
                self.working_config['listeners'] = []
            self.working_config['listeners'].append(listener_data)
            self.refresh_listener_list()
    
    def edit_listener(self):
        """Edit selected listener"""
        current = self.listener_list.currentItem()
        if not current:
            return
        
        index = current.data(Qt.UserRole)
        listeners = self.working_config.get('listeners', [])
        if 0 <= index < len(listeners):
            dialog = ListenerEditDialog(self, listeners[index])
            if dialog.exec():
                listeners[index] = dialog.get_listener_data()
                self.refresh_listener_list()
    
    def delete_listener(self):
        """Delete selected listener"""
        current = self.listener_list.currentItem()
        if not current:
            return
        
        reply = QMessageBox.question(
            self, 
            T("msg_confirm_delete", "Confirm Delete"),
            T("msg_confirm_delete_listener", "Are you sure you want to delete this listener?"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            index = current.data(Qt.UserRole)
            listeners = self.working_config.get('listeners', [])
            if 0 <= index < len(listeners):
                listeners.pop(index)
                self.refresh_listener_list()
    
    def save_data(self):
        """Save ANPR Listener configuration"""
        # Create picture directories for all listeners
        listeners = self.working_config.get('listeners', [])
        for listener in listeners:
            pic_path = listener.get('picture_path', '')
            if pic_path and not os.path.exists(pic_path):
                try:
                    os.makedirs(pic_path, exist_ok=True)
                except Exception as e:
                    QMessageBox.warning(self, T("msg_error"), f"Could not create picture directory for {listener.get('name', 'listener')}: {e}")
                    return
        
        # Create clean config with only listeners list
        clean_listener_config = {
            'listeners': listeners
        }
        
        # Keep description if it exists (for backward compatibility info)
        if 'description' in self.working_config:
            clean_listener_config['description'] = self.working_config['description']
        
        full_config = ConfigManager.load_config()
        full_config['listener'] = clean_listener_config  # Changed from 'anpr_listener' to 'listener'
        ConfigManager.save_config(full_config)
        
        QMessageBox.information(self, T("msg_success"), T("msg_settings_saved", "Settings saved. Changes apply immediately to new requests."))
        self.accept()


class ListenerEditDialog(QDialog):
    """Dialog for adding/editing a listener"""
    def __init__(self, parent=None, listener_data=None):
        super().__init__(parent)
        self.setWindowTitle(T("title_edit_listener", "Edit Listener") if listener_data else T("title_add_listener", "Add Listener"))
        self.resize(500, 450)
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Listener Name
        self.name_edit = QLineEdit()
        form_layout.addRow(T("lbl_listener_name", "Listener Name"), self.name_edit)
        
        # Enabled Checkbox
        self.enabled_cb = QCheckBox(T("lbl_enable_listener", "Enable this listener"))
        form_layout.addRow("", self.enabled_cb)
        
        # URL Path
        self.url_edit = QLineEdit()
        form_layout.addRow(T("lbl_listener_url", "Listener URL Path"), self.url_edit)
        
        # Plate Tag (XML tag to read from camera)
        self.plate_tag_edit = QLineEdit()
        form_layout.addRow(T("lbl_plate_tag", "Plate XML Tag"), self.plate_tag_edit)
        
        # Response Tag (tag name in response JSON)
        self.response_tag_edit = QLineEdit()
        form_layout.addRow(T("lbl_response_tag", "Response Tag"), self.response_tag_edit)
        
        # Time Tolerance
        self.tolerance_edit = QLineEdit()
        form_layout.addRow(T("lbl_tolerance_minutes", "Time Tolerance (min)"), self.tolerance_edit)
        
        # Timeout (seconds)
        self.timeout_edit = QLineEdit()
        form_layout.addRow(T("lbl_timeout_seconds", "Timeout (seconds)"), self.timeout_edit)
        
        # Picture Path Selection
        path_layout = QHBoxLayout()
        self.pic_path_edit = QLineEdit()
        self.pic_path_btn = QPushButton(T("btn_browse", "Browse..."))
        self.pic_path_btn.clicked.connect(self.select_picture_path)
        path_layout.addWidget(self.pic_path_edit)
        path_layout.addWidget(self.pic_path_btn)
        form_layout.addRow(T("lbl_save_pictures", "Save Pictures To"), path_layout)
        
        layout.addLayout(form_layout)
        
        # Load data if editing
        if listener_data:
            self.name_edit.setText(listener_data.get('name', ''))
            self.enabled_cb.setChecked(listener_data.get('enabled', True))
            self.url_edit.setText(str(listener_data.get('url', '/anpr/notify')))
            self.plate_tag_edit.setText(str(listener_data.get('plate_tag', 'licensePlate')))
            self.response_tag_edit.setText(str(listener_data.get('response_tag', '')))
            self.tolerance_edit.setText(str(listener_data.get('tolerance_minutes', 5)))
            self.timeout_edit.setText(str(listener_data.get('timeout_seconds', 60)))
            self.pic_path_edit.setText(str(listener_data.get('picture_path', '')))
        else:
            # Defaults for new listener
            self.enabled_cb.setChecked(True)
            self.url_edit.setText("/anpr/notify")
            self.plate_tag_edit.setText("licensePlate")
            self.response_tag_edit.setText("")
            self.tolerance_edit.setText("5")
            self.timeout_edit.setText("60")
            default_pics = os.path.join(os.path.expanduser("~"), "ANPR_Pictures")
            self.pic_path_edit.setText(default_pics)
        
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.Ok).setText(T("btn_ok"))
        btns.button(QDialogButtonBox.Cancel).setText(T("btn_cancel"))
        layout.addWidget(btns)
    
    def select_picture_path(self):
        """Select picture directory"""
        path = QFileDialog.getExistingDirectory(self, T("title_select_picture_dir", "Select Directory for ANPR Pictures"), self.pic_path_edit.text() or os.path.expanduser("~"))
        if path:
            self.pic_path_edit.setText(path)
    
    def get_listener_data(self):
        """Get listener data from form"""
        try:
            tolerance = float(self.tolerance_edit.text())
        except:
            tolerance = 5.0
        
        try:
            timeout = float(self.timeout_edit.text())
        except:
            timeout = 60.0
        
        url = self.url_edit.text()
        if not url.startswith('/'):
            url = '/' + url
        
        return {
            'name': self.name_edit.text() or 'Listener',
            'enabled': self.enabled_cb.isChecked(),
            'url': url,
            'plate_tag': self.plate_tag_edit.text() or 'licensePlate',
            'response_tag': self.response_tag_edit.text().strip(),
            'tolerance_minutes': tolerance,
            'timeout_seconds': timeout,
            'picture_path': self.pic_path_edit.text() or os.path.join(os.path.expanduser("~"), "ANPR_Pictures")
        }

# --- Background Server Thread ---

class MainWindow(QMainWindow):
    request_signal = Signal(dict)
    request_start_signal = Signal(dict)
    anpr_signal = Signal(str)
    
    # Temporary storage for request start data (for cross-thread calls)
    _pending_request_start_data = None
    
    # Store last isapi_result to persist indicator colors
    _last_isapi_result = None

    def __init__(self):
        super().__init__()
        
        # Connect signals
        self.request_signal.connect(self.update_ui_from_request)
        self.request_start_signal.connect(self.update_ui_from_request_start)
        self.anpr_signal.connect(self.update_anpr_display)
        
        # Setup Server callbacks
        opscalesrv.ON_REQUEST_CALLBACK = self.handle_request
        opscalesrv.ON_START_CALLBACK = self.handle_request_start
        
        # Register ANPR Listener callback
        from . import anpr_listener
        anpr_listener.register_callback(self.handle_anpr_listener_callback)

        
        # Load Language
        config = ConfigManager.load_config()
        lang = config.get('settings', {}).get('language', 'en')
        _translator.load_language(lang)
        
        # License Check (Read from license.key file)
        if not licensing.verify_license():
            lic_dlg = LicenseDialog(self)
            if not lic_dlg.exec():
                sys.exit(0)

                
        self.setWindowTitle(T("app_title"))

        self.resize(480, 320)
        
        # Set Window Icon
        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'opscalesrv.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Menu Bar
        self.create_menu_bar()
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Header Area
        header_layout = QHBoxLayout()
        
        # Indicators Container (moved to left side where server name was)
        indicators_vbox = QVBoxLayout()
        indicators_vbox.setSpacing(2)
        
        # Row 1: TEST, SERIAL, LOG
        row1_layout = QHBoxLayout()
        self.indicator_test = QLabel("TEST")
        self.indicator_serial = QLabel("SERIAL")
        self.indicator_log = QLabel("LOG")
        for lbl in [self.indicator_test, self.indicator_serial, self.indicator_log]:
            lbl.setStyleSheet("font-size: 10px; color: #555555; font-weight: bold; margin-right: 8px; padding: 0px; border: none;")
            row1_layout.addWidget(lbl)
            
        # Row 2: ISAPI, QUERY, LISTENER
        row2_layout = QHBoxLayout()
        self.indicator_isapi = QLabel("ISAPI")
        self.indicator_query = QLabel("QUERY")
        self.indicator_listener = QLabel("LISTENER")
        for lbl in [self.indicator_isapi, self.indicator_query, self.indicator_listener]:
            lbl.setStyleSheet("font-size: 10px; color: #555555; font-weight: bold; margin-right: 8px; padding: 0px; border: none;")
            row2_layout.addWidget(lbl)
            
        indicators_vbox.addLayout(row1_layout)
        indicators_vbox.addLayout(row2_layout)
        
        header_layout.addLayout(indicators_vbox)
        header_layout.addStretch()
        
        # Traffic Light on the right side of header
        self.header_traffic_light = TrafficLight()
        header_layout.addWidget(self.header_traffic_light, 0, Qt.AlignRight)
        
        main_layout.addLayout(header_layout)

        
        # Content Area - Card Like
        content_frame = ModernFrame()
        content_layout = QHBoxLayout(content_frame)  # Changed to horizontal
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Left side - Serial port value (top)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(8)
        
        self.value_label = QLabel("--.--")
        self.value_label.setFont(QFont("Segoe UI", 48, QFont.Bold))
        self.value_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.value_label.setStyleSheet("color: #BB86FC;")
        self.value_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        self.msg_label = QLabel(T("lbl_no_data"))
        self.msg_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.msg_label.setStyleSheet("color: #888888; font-size: 13px;")
        self.msg_label.setWordWrap(True)  # Enable word wrap
        self.msg_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        # Function to sync msg_label width with value_label
        def sync_msg_width():
            if self.value_label.width() > 0:
                self.msg_label.setMaximumWidth(self.value_label.width())
        
        # Override value_label's resizeEvent to sync msg_label width
        original_resize = self.value_label.resizeEvent
        def resize_with_sync(event):
            original_resize(event)
            sync_msg_width()
        
        self.value_label.resizeEvent = resize_with_sync
        
        # Also sync after widgets are shown
        QTimer.singleShot(100, sync_msg_width)
        
        self.time_label = QLabel("")
        self.time_label.setAlignment(Qt.AlignLeft)
        self.time_label.setStyleSheet("color: #666666; font-size: 11px;")
        self.time_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        left_layout.addWidget(self.value_label)
        left_layout.addWidget(self.msg_label)
        left_layout.addWidget(self.time_label)
        left_layout.addStretch()  # Push content to top
        
        content_layout.addLayout(left_layout, 1)  # Left side takes 1 part
        
        # Right side - Plates (scrollable)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Scroll area for multiple plates - full height
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.scroll_area.setMinimumWidth(250)  # Minimum width for plates
        self.scroll_area.setMaximumWidth(350)  # Maximum width for plates
        self.scroll_area.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        scroll_widget.setMinimumWidth(230)  # Ensure widget has minimum width
        self.plates_layout = QVBoxLayout(scroll_widget)
        self.plates_layout.setSpacing(4)  # Reduced spacing for list view
        self.plates_layout.setContentsMargins(5, 5, 5, 5)  # Small margins
        
        self.scroll_area.setWidget(scroll_widget)
        right_layout.addWidget(self.scroll_area, 1)  # Take all available space
        
        content_layout.addLayout(right_layout, 0)  # Right side takes less space
        
        # Store plate widgets for updates
        self.plate_widgets = {}  # {response_tag: widget}
        
        main_layout.addWidget(content_frame)
        
        # Status Bar - Show server IP and port
        import socket
        server_ip = "Unknown"
        try:
            # Get local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            server_ip = s.getsockname()[0]
            s.close()
        except:
            try:
                server_ip = socket.gethostbyname(socket.gethostname())
            except:
                pass
        
        # Get server port from config
        server_port = config.get('settings', {}).get('port', 7373)
        
        self.status_bar = QLabel(f"Server: {server_ip}:{server_port} | {T('status_initial')}")
        self.status_bar.setStyleSheet("color: #666666; font-size: 11px;")
        self.status_bar.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_bar)
        
        # Initial indicator update (after all widgets are created)
        self.update_indicators()

        # Timers & Signals
        self.reset_timer = QTimer()
        self.reset_timer.timeout.connect(self.reset_state)
        
        # Timer to periodically update indicators (especially SERIAL status)
        self.indicator_update_timer = QTimer()
        self.indicator_update_timer.timeout.connect(self.update_indicators)
        self.indicator_update_timer.start(1000)  # Update every 1 second
        
        signal_manager.request_received.connect(self.handle_request)
        
        # Start Server Daemon Thread
        self.server_thread = ServerThread()
        self.server_thread.start()

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # Server Menu
        server_menu = menubar.addMenu(T("menu_server"))
        
        # Restart Action
        restart_act = QAction(T("act_restart"), self)
        restart_act.triggered.connect(self.restart_server)
        server_menu.addAction(restart_act)
        
        # Test Mode Action (Moved to Server)
        self.test_mode_act = QAction(T("act_test_mode"), self, checkable=True)
        self.test_mode_act.setChecked(opscalesrv.TEST_MODE)
        self.test_mode_act.triggered.connect(self.toggle_test_mode)
        server_menu.addAction(self.test_mode_act)
        
        server_menu.addSeparator()
        
        # Set Password Action
        pwd_act = QAction(T("act_set_password"), self)
        pwd_act.triggered.connect(self.open_set_password)
        server_menu.addAction(pwd_act)
        
        # ABAP Generation Action
        abap_act = QAction(T("act_gen_abap"), self)
        abap_act.triggered.connect(self.generate_abap_code)
        server_menu.addAction(abap_act)
        
        server_menu.addSeparator()
        
        # Exit Action
        exit_act = QAction(T("act_exit"), self)
        exit_act.triggered.connect(self.close)
        server_menu.addAction(exit_act)
        
        # Settings Menu
        settings_menu = menubar.addMenu(T("menu_settings"))
        
        # 1. Serial Port
        serial_act = QAction(T("act_serial"), self)
        serial_act.triggered.connect(self.open_serial_settings)
        settings_menu.addAction(serial_act)
        
        # 2. ANPR Listener
        anpr_listener_act = QAction(T("act_anpr_listener"), self)
        anpr_listener_act.triggered.connect(self.open_anpr_listener_settings)
        settings_menu.addAction(anpr_listener_act)
        
        # 3. ANPR Query
        anpr_act = QAction(T("act_anpr"), self)
        anpr_act.triggered.connect(self.open_anpr_settings)
        settings_menu.addAction(anpr_act)
        
        # 4. Allowed Hosts
        hosts_act = QAction(T("act_hosts"), self)
        hosts_act.triggered.connect(self.open_hosts_settings)
        settings_menu.addAction(hosts_act)
        
        # 5. General Settings
        general_act = QAction(T("act_general"), self)
        general_act.triggered.connect(self.open_general_settings)
        settings_menu.addAction(general_act)
        
        settings_menu.addSeparator()
        
        # 6. Reset
        reset_act = QAction(T("act_reset_settings", "Reset Settings"), self)
        reset_act.triggered.connect(self.reset_settings)
        settings_menu.addAction(reset_act)
        
        # Logs Menu
        logs_menu = menubar.addMenu(T("menu_logs", "Logs"))
        
        show_log_act = QAction(T("act_show_log", "Show Logs"), self)
        show_log_act.triggered.connect(self.show_logs)
        logs_menu.addAction(show_log_act)
        
        clear_log_act = QAction(T("act_clear_log", "Clear Logs"), self)
        clear_log_act.triggered.connect(self.clear_logs)
        logs_menu.addAction(clear_log_act)
        
        # Help Menu
        help_menu = menubar.addMenu(T("menu_help"))
        
        about_act = QAction(T("act_about"), self)
        about_act.triggered.connect(self.show_about)
        help_menu.addAction(about_act)

    def generate_abap_code(self):
        if not self.check_password():
            return
            
        dir_path = QFileDialog.getExistingDirectory(self, T("title_select_abap_dir"))
        if dir_path:
            try:
                # We need to manually invoke the copy logic or reimplement it since copy_abap_files 
                # in __init__.py targets os.getcwd() and is a bit rigid.
                # Let's read from package source and write to selected dir.
                
                package_dir = os.path.dirname(opscalesrv.__file__)
                abap_source_dir = os.path.join(package_dir, 'abap')
                
                if not os.path.exists(abap_source_dir):
                    QMessageBox.warning(self, T("msg_error"), f"{T('msg_abap_dir_not_found')}: {abap_source_dir}")
                    return

                files = [f for f in os.listdir(abap_source_dir) if f.endswith('.abap')]
                if not files:
                    QMessageBox.warning(self, T("msg_error"), T("msg_no_abap_files"))
                    return
                
                import shutil
                copied_count = 0
                for f in files:
                    src = os.path.join(abap_source_dir, f)
                    dst = os.path.join(dir_path, f)
                    shutil.copy2(src, dst)
                    copied_count += 1
                
                QMessageBox.information(self, T("msg_success"), f"{T('msg_abap_saved_to')}:\n{dir_path}")
                
            except Exception as e:
                QMessageBox.critical(self, T("msg_error"), f"{T('msg_failed_gen_abap')}: {e}")

    def restart_server(self):
        # Password check removed as per user request
        # if not self.check_password():
        #     return

        self.status_bar.setText(T("status_restarting"))
        if hasattr(self, 'header_traffic_light'):
            self.header_traffic_light.set_state("IDLE")
        QApplication.processEvents()
        
        # Stop existing server
        opscalesrv.stop_server()
        
        # Wait a bit for shutdown
        import time
        time.sleep(0.5)
        
        # Start new thread
        self.server_thread = ServerThread()
        self.server_thread.start()
        
        # Update status
        config = ConfigManager.load_config()
        self.update_indicators()
        port = config.get('settings', {}).get('port', 7373)
        self.status_bar.setText(f"{T('status_server_restarted')} | {T('lbl_port')}: {port} | {T('status_waiting_requests')}")
        QMessageBox.information(self, T("title_server_restarted"), f"{T('msg_server_restarted_on_port')} {port}")


    def handle_request(self, data):
        """
        Callback from background server thread.
        Emit signal to update UI on main thread.
        """
        self.request_signal.emit(data)

    def handle_request_start(self, data_or_ip, path=None):
        """Called when a request begins processing - thread-safe"""
        # Handle both dict and separate parameters
        if isinstance(data_or_ip, dict):
            data = data_or_ip
        else:
            data = {'client_ip': data_or_ip, 'path': path}
        
        logger = logging.getLogger(__name__)
        logger.info(f"handle_request_start called from thread, data: {data}")
        
        # Store data in instance variable for cross-thread access
        self._pending_request_start_data = data
        
        # Emit signal first (most reliable for cross-thread communication)
        self.request_start_signal.emit(data)
        logger.info("request_start_signal emitted")
        
        # Also use QMetaObject.invokeMethod as backup
        QMetaObject.invokeMethod(
            self,
            "_process_request_start",
            Qt.QueuedConnection
        )
        logger.info("QMetaObject.invokeMethod called for _process_request_start")
    
    def _process_request_start(self):
        """Internal method called on main thread to process request start"""
        logger = logging.getLogger(__name__)
        logger.info("_process_request_start called on main thread")
        if self._pending_request_start_data:
            logger.info(f"Processing request start with data: {self._pending_request_start_data}")
            self.update_ui_from_request_start(self._pending_request_start_data)
            self._pending_request_start_data = None
        else:
            logger.warning("_process_request_start called but no pending data")

    def handle_anpr_listener_callback(self, plate):
        """Callback from ANPR listener when a plate is captured"""
        self.anpr_signal.emit(plate)
        
    def update_ui_from_request_start(self, data=None):
        """
        Update UI when request starts (on main thread)
        This method is called via QMetaObject.invokeMethod from HTTP server thread
        """
        try:
            # Ensure we have valid data
            if data is None:
                data = {}
            
            logger = logging.getLogger(__name__)
            logger.info(f"update_ui_from_request_start called with data: {data}")
            
            # Update traffic light to PROCESSING state (red pulsing)
            # This is the traffic light on the right side of header (next to indicators)
            if hasattr(self, 'header_traffic_light') and self.header_traffic_light:
                logger.info("Setting header_traffic_light to PROCESSING state (should be pulsing red)")
                logger.info(f"Traffic light widget exists: {self.header_traffic_light is not None}")
                logger.info(f"Traffic light current state before: {getattr(self.header_traffic_light, 'state', 'unknown')}")
                
                # Set state to PROCESSING
                self.header_traffic_light.set_state("PROCESSING")
                
                # Verify state was set and timer started
                logger.info(f"Traffic light state after set_state: {getattr(self.header_traffic_light, 'state', 'unknown')}")
                if hasattr(self.header_traffic_light, 'pulse_timer'):
                    is_active = self.header_traffic_light.pulse_timer.isActive()
                    logger.info(f"Traffic light pulse_timer active: {is_active}")
                    if not is_active:
                        logger.error("ERROR: pulse_timer is NOT active after set_state('PROCESSING')!")
                
                # Force immediate repaint
                self.header_traffic_light.repaint()
                QApplication.processEvents()
                logger.info("Traffic light state set to PROCESSING and repainted")
            else:
                logger.warning("header_traffic_light not found or not initialized")
            
            self.msg_label.setText(T("status_processing", "Processing..."))
            self.value_label.setText("--.--")
            
            # Clear plates during processing
            for widget in list(self.plate_widgets.values()):
                widget.setParent(None)
            self.plate_widgets.clear()
            
            # Clear layout
            while self.plates_layout.count():
                item = self.plates_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            processing_label = QLabel(T("status_processing", "Processing..."))
            processing_label.setAlignment(Qt.AlignCenter)
            processing_label.setStyleSheet("color: #888888; font-size: 16px; padding: 20px;")
            self.plates_layout.addWidget(processing_label)
            self.status_bar.setText(f"{T('status_processing')}... ({data.get('path', '')})")
            QApplication.processEvents()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in update_ui_from_request_start: {e}", exc_info=True)

    def create_plate_card(self, response_tag, plate_value):
        """Create a simple label for a plate (no frame, just text)"""
        plate_label = QLabel(plate_value)
        plate_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 18px;
            font-weight: bold;
            font-family: 'Courier New', monospace;
            background-color: transparent;
            padding: 5px 0px;
        """)
        plate_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        plate_label.setWordWrap(False)  # Prevent text wrapping
        plate_label.setMinimumWidth(200)  # Ensure minimum width
        
        return plate_label
    
    def update_anpr_display(self, plate):
        """
        Update UI immediately when an ANPR plate is captured via listener
        """
        # This is called from listener callback, we'll update in the main request handler
        self.msg_label.setText(f"ANPR Capture: {plate}")
        
        # Flash status bar
        self.status_bar.setText(f"ANPR Listener: Captured {plate}")



    def update_ui_from_request(self, data):

        """
        Slot to update UI on main thread
        """
        # Ignore favicon requests to prevent overwriting relevant data
        path = data.get('path', '')
        if path and 'favicon.ico' in path:
            return

        # robust data extraction
        resp_data = data.get('response_data')
        
        # Determine if we have a wrapped response (dict with 'message') or flat (just message_data)
        if isinstance(resp_data, dict) and 'message' in resp_data:
            msg_dict = resp_data['message']
        else:
            msg_dict = resp_data
            
        if not msg_dict or not isinstance(msg_dict, dict):
            # Probably an access check (None) or access denied
            client = f"{data.get('client_ip')}"
            status = data.get('status')
            if status: 
                self.status_bar.setText(f"{T('status_req_from')}: {client} | {T('status_path')}: {path} | {T('status_status')}: {status}")
            return

        # Success flags
        serial_status = msg_dict.get('result', 'FAIL')
        plate_val = msg_dict.get('plate', 'NO_PLATE')
        isapi_result = msg_dict.get('isapi_result', 'OK')
        
        # Correctly determine ANPR status
        # Success = not an error (NO_PLATE is not an error)
        anpr_errors = ["ANPR_ERROR", "CAM_ERROR", "ERROR", "TIMEOUT"]
        anpr_ok = (plate_val not in anpr_errors)
        
        # Serial status
        serial_ok = (serial_status in ['OK', 'DISABLED'])
        
        # ISAPI result status
        isapi_ok = (isapi_result in ['OK', 'DISABLED'])
        
        # Main light: Both must be okay (DISABLED counts as okay)
        is_ok = (serial_ok and anpr_ok and isapi_ok)
        
        # Response arrived - set to final state immediately
        # (The light should already be pulsing from request start)
        if hasattr(self, 'header_traffic_light'):
            self.header_traffic_light.set_state(is_ok)
        
        # Update header indicators (SERIAL and LOG are already updated via update_indicators)
        # ISAPI, QUERY, LISTENER indicators are updated via update_indicators based on ANPR mode and isapi_result
        self.update_indicators_with_isapi_result(isapi_result)

        # Update Status Bar with server IP
        client = f"{data.get('client_ip')}"
        curr_status = data.get('status', serial_status)
        
        # Get server IP address
        import socket
        server_ip = "Unknown"
        try:
            # Get local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            server_ip = s.getsockname()[0]
            s.close()
        except:
            try:
                server_ip = socket.gethostbyname(socket.gethostname())
            except:
                pass
        
        # Get server port from config
        config = ConfigManager.load_config()
        server_port = config.get('settings', {}).get('port', 7373)
        
        self.status_bar.setText(f"Server: {server_ip}:{server_port} | {T('status_req_from')}: {client} | {T('status_path')}: {path} | {T('status_status')}: {curr_status}")
        
        try:
            # Update Time
            if isinstance(resp_data, dict) and resp_data.get('timestamp'):
                ts = resp_data.get('timestamp')
                try: from datetime import datetime; dt = datetime.fromisoformat(ts); ts = dt.strftime("%Y-%m-%d %H:%M:%S")
                except: pass
                self.time_label.setText(ts)
            else:
                from datetime import datetime; self.time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
            # Update Plates Display - show all plates from response
            # Clear existing plate widgets
            for widget in list(self.plate_widgets.values()):
                widget.setParent(None)
            self.plate_widgets.clear()
            
            # Clear layout
            while self.plates_layout.count():
                item = self.plates_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Extract all plates from message_data (response_tag: plate pairs)
            plates_found = {}
            for key, value in msg_dict.items():
                # Skip standard fields, only get plate fields (response_tags)
                if key not in ['value', 'msg', 'mode', 'result', 'plate'] and value:
                    # Check if it looks like a plate (not empty, not error codes)
                    if value not in ["NO_PLATE", "ANPR_DISABLED", "DIRECTION_DISABLED", "ANPR_ERROR", "CAM_ERROR", "ERROR", "TIMEOUT"]:
                        plates_found[key] = value
            
            # Also check legacy 'plate' field if no response_tag plates found
            if not plates_found and plate_val and plate_val not in ["NO_PLATE", "ANPR_DISABLED", "DIRECTION_DISABLED", "ANPR_ERROR", "CAM_ERROR", "ERROR", "TIMEOUT"]:
                plates_found['plate'] = plate_val
            
            # Create plate cards
            if plates_found:
                for response_tag, plate_value in sorted(plates_found.items()):
                    plate_card = self.create_plate_card(response_tag, plate_value)
                    self.plates_layout.addWidget(plate_card)
                    self.plate_widgets[response_tag] = plate_card
            else:
                # Show "No Plate" message
                no_plate_label = QLabel(T("lbl_no_plate"))
                no_plate_label.setAlignment(Qt.AlignCenter)
                no_plate_label.setStyleSheet("color: #888888; font-size: 16px; padding: 20px;")
                self.plates_layout.addWidget(no_plate_label)

            # Update Message Detail
            txt = msg_dict.get('msg', T('msg_data_received'))
            self.msg_label.setText(txt)
            # Sync width with value_label after text update
            if self.value_label.width() > 0:
                self.msg_label.setMaximumWidth(self.value_label.width())
            
            # Update Value Display
            val = msg_dict.get('value')
            if val is not None:
                try:
                    v_float = float(val)
                    if v_float < 0:
                        self.value_label.setText("Error")
                        self.value_label.setStyleSheet("color: #FF5252; font-size: 42px; font-weight: bold;")
                    else:
                        self.value_label.setText(f"{v_float:,.2f}")
                        self.value_label.setStyleSheet("color: #03DAC6; font-size: 42px; font-weight: bold;")
                except:
                    self.value_label.setText(str(val))
            else:
                self.value_label.setText("--.--")

        except Exception as e:
            print(f"Error in update_ui_from_request detail: {e}")


    def reset_state(self):
        if hasattr(self, 'header_traffic_light'):
            self.header_traffic_light.set_state("IDLE")

        self.status_bar.setText(T("status_idle_waiting"))
        self.reset_timer.stop()
        
        # Clear plates
        for widget in list(self.plate_widgets.values()):
            widget.setParent(None)
        self.plate_widgets.clear()
        
        # Clear layout
        while self.plates_layout.count():
            item = self.plates_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def toggle_test_mode(self, checked):
        opscalesrv.TEST_MODE = checked
        if checked:
            self.status_bar.setText(T("status_test_mode"))
        else:
            self.status_bar.setText(T("status_serial_mode"))
        
        self.update_indicators()

    def update_indicators(self):
        """Update indicators (TEST, SERIAL, LOG, ISAPI, QUERY, LISTENER) based on current state"""
        config = ConfigManager.load_config()
        
        # TEST indicator - RED if ON
        is_test = opscalesrv.TEST_MODE
        color_test = "#FF5252" if is_test else "#555555"
        self.indicator_test.setStyleSheet(f"font-size: 10px; color: {color_test}; font-weight: bold; margin-right: 8px; padding: 0px; border: none;")
        
        # Helper to get color: if test mode is on, everything else is gray.
        def get_ind_color(is_enabled):
            if is_test: return "#555555"
            # Yellow (#FFC107) if enabled, gray if disabled
            return "#FFC107" if is_enabled else "#555555"

        # SERIAL indicator - Green if OK, Red if error, Yellow if enabled but not monitored
        serial_status = opscalesrv.SERIAL_STATUS
        serial_enabled = config.get('settings', {}).get('serial', True)
        
        if is_test:
            # Test mode: Green if serial is enabled and status is OK, otherwise gray
            if serial_enabled and serial_status is True:
                color_serial = "#00E676"  # Green
            else:
                color_serial = "#555555"  # Gray
        else:
            # Normal mode: Green if OK, Red if error, Yellow if enabled but status unknown
            if serial_status is True:
                color_serial = "#00E676"  # Green - OK
            elif serial_status is False:
                color_serial = "#FF5252"  # Red - Error
            elif serial_enabled:
                color_serial = "#FFC107"  # Yellow - Enabled but status unknown
            else:
                color_serial = "#555555"  # Gray - Disabled
        
        self.indicator_serial.setStyleSheet(f"font-size: 10px; color: {color_serial}; font-weight: bold; margin-right: 8px; padding: 0px; border: none;")

        # LOG indicator - Yellow if enabled
        log_enabled = config.get('settings', {}).get('log_all_requests', False)
        color_log = get_ind_color(log_enabled)
        self.indicator_log.setStyleSheet(f"font-size: 10px; color: {color_log}; font-weight: bold; margin-right: 8px; padding: 0px; border: none;")

        # ANPR(ISAPI) indicators based on mode
        anpr_mode = config.get('settings', {}).get('isapi', 'disabled')
        
        if is_test:
            # Test mode: all gray
            color_isapi = "#555555"
            color_query = "#555555"
            color_listener = "#555555"
        elif anpr_mode == 'disabled':
            # Disabled: all gray
            color_isapi = "#555555"
            color_query = "#555555"
            color_listener = "#555555"
        elif anpr_mode == 'query':
            # Query mode: ISAPI green, QUERY yellow (or red if FAIL)
            color_isapi = "#00E676"
            if hasattr(self, '_last_isapi_result') and self._last_isapi_result == 'FAIL':
                color_query = "#FF5252"  # Red if FAIL
            else:
                color_query = "#FFC107"  # Yellow if OK
            color_listener = "#555555"
        elif anpr_mode == 'listen':
            # Listener mode: ISAPI green, LISTENER yellow (or red if FAIL)
            color_isapi = "#00E676"
            color_query = "#555555"
            if hasattr(self, '_last_isapi_result') and self._last_isapi_result == 'FAIL':
                color_listener = "#FF5252"  # Red if FAIL
            else:
                color_listener = "#FFC107"  # Yellow if OK
        else:
            # Unknown mode: all gray
            color_isapi = "#555555"
            color_query = "#555555"
            color_listener = "#555555"
        
        self.indicator_isapi.setStyleSheet(f"font-size: 10px; color: {color_isapi}; font-weight: bold; margin-right: 8px; padding: 0px; border: none;")
        self.indicator_query.setStyleSheet(f"font-size: 10px; color: {color_query}; font-weight: bold; margin-right: 8px; padding: 0px; border: none;")
        self.indicator_listener.setStyleSheet(f"font-size: 10px; color: {color_listener}; font-weight: bold; margin-right: 8px; padding: 0px; border: none;")
        
        # Show/hide plate scrollbar based on ISAPI mode
        if hasattr(self, 'scroll_area'):
            if anpr_mode == 'disabled':
                self.scroll_area.hide()
            else:
                self.scroll_area.show()
        
        # Header traffic light state is updated directly in other methods
    
    def update_indicators_with_isapi_result(self, isapi_result):
        """Update QUERY or LISTENER indicator to red if isapi_result is FAIL"""
        # Store the last isapi_result so update_indicators() can use it
        self._last_isapi_result = isapi_result
        
        # Immediately update indicators to reflect the new result
        self.update_indicators()





    def open_serial_settings(self):
        if self.check_password():
            if SerialSettingsDialog(self).exec():
                self.update_indicators()
                QMessageBox.information(self, T("title_restart_required"), T("msg_restart_required"))


    def open_hosts_settings(self):
        if self.check_password():
            if AllowedHostsDialog(self).exec():
                # Allowed hosts might update live if I reload config in server loop, but server loads only once.
                self.update_indicators()
                QMessageBox.information(self, T("title_restart_required"), T("msg_restart_required"))


    def open_general_settings(self):
        if self.check_password():
            if GeneralSettingsDialog(self).exec():
                self.update_indicators()
                QMessageBox.information(self, T("title_restart_required"), T("msg_restart_required"))


    def open_anpr_settings(self):
        if self.check_password():
            if ANPRSettingsDialog(self).exec():
                self.update_indicators()
                QMessageBox.information(self, T("title_restart_required"), T("msg_restart_required"))

    def open_anpr_listener_settings(self):
        if self.check_password():
            if ANPRListenerSettingsDialog(self).exec():
                QMessageBox.information(self, T("title_restart_required"), T("msg_restart_required"))


    def show_logs(self):
        LogViewerDialog(self).exec()

    def clear_logs(self):
        if self.check_password():
            config = ConfigManager.load_config()
            log_file = config.get('settings', {}).get('log_file', 'requests.log')
            
            try:
                # Open with 'w' to truncate
                with open(log_file, 'w', encoding='utf-8') as f:
                    pass
                QMessageBox.information(self, "Success", T("msg_logs_cleared", "Logs cleared."))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear logs: {e}")

    def check_password(self):
        config = ConfigManager.load_config()
        stored_hash = config.get('settings', {}).get('password')
        
        if not stored_hash:
            return True
            
        dlg = CheckPasswordDialog(self)
        if dlg.exec():
            pwd = dlg.get_password()
            pwd_hash = hashlib.sha256(pwd.encode('utf-8')).hexdigest()
            if pwd_hash == stored_hash:
                return True
            else:
                QMessageBox.warning(self, T("msg_access_denied"), T("msg_incorrect_pwd"))
                return False
        return False

    def show_about(self):
        text = """
        <h2 style='color: #BB86FC'>Opriori Scale Server</h2>
        <p><b>ANPR supported</b></p>
        <p>Version 1.0.36</p>
        <br>
        <p>Altay Kireççi (c)(p) 12192025</p>
        <p><a href='http://www.opriori.com.tr' style='color: #03DAC6'>www.opriori.com.tr</a></p>
        """
        QMessageBox.about(self, T("act_about"), text)

    def reset_settings(self):
        """Reset all settings to default values"""
        if not self.check_password():
            return
        
        # Confirm reset
        reply = QMessageBox.question(
            self, 
            T("title_reset_settings", "Reset Settings"),
            T("msg_confirm_reset", "Are you sure you want to reset all settings to default values?\n\nThis will:\n- Reset all configuration to defaults\n- Remove password protection\n- Require server restart\n\nThis action cannot be undone."),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                ConfigManager.reset_to_default()
                QMessageBox.information(
                    self, 
                    T("msg_success", "Success"),
                    T("msg_settings_reset", "Settings have been reset to default values.\n\nPlease restart the server for changes to take effect.")
                )
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    T("msg_error", "Error"),
                    f"{T('msg_reset_failed', 'Failed to reset settings')}: {e}"
                )

    def open_set_password(self):
        config = ConfigManager.load_config()
        stored_hash = config.get('settings', {}).get('password')
        
        dlg = SetPasswordDialog(has_current_password=bool(stored_hash), parent=self)
        if dlg.exec():
            current, new = dlg.get_data()
            
            if stored_hash:
                current_hash = hashlib.sha256(current.encode('utf-8')).hexdigest()
                if current_hash != stored_hash:
                    QMessageBox.warning(self, T("msg_error"), T("msg_incorrect_pwd"))
                    return
            
            # Save new password
            settings = config.get('settings', {})
            if new:
                settings['password'] = hashlib.sha256(new.encode('utf-8')).hexdigest()
                QMessageBox.information(self, T("msg_success"), T("msg_pwd_set"))
            else:
                # If existing password and new is empty, remove password protection?? 
                # Or just treat empty as no password? Let's assume empty means remove.
                if 'password' in settings:
                    del settings['password']
                QMessageBox.information(self, T("msg_success"), T("msg_pwd_removed"))
            
            config['settings'] = settings
            ConfigManager.save_config(config)

def main():
    app = QApplication(sys.argv)
    
    # Workspace Setup Logic (One-time)
    if not paths.is_path_setup():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(T("title_setup", "Setup Required"))
        msg.setText(T("msg_setup_workspace", "Please select a folder for OpScale Server data (config, logs, license)."))
        msg.setInformativeText("This folder will store your settings and data cross-platform.")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        
        if msg.exec() == QMessageBox.Ok:
            folder = QFileDialog.getExistingDirectory(None, T("title_select_folder", "Select Workspace Folder"))
            if folder:
                paths.set_base_path(folder)
            else:
                sys.exit(0)
        else:
            sys.exit(0)

    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
