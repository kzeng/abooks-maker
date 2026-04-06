from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QPushButton, 
    QLabel, QComboBox, QProgressBar, QFileDialog, QMessageBox,
    QTabWidget, QGroupBox, QRadioButton, QFormLayout, QTextEdit, QCheckBox, QListWidget,
    QSlider, QListWidgetItem, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QSettings, QTimer, Signal, QPoint, QUrl
from PySide6.QtGui import QFont, QPixmap, QIcon
import os
import sys
from .converter import ConvertThread, PreviewThread, EDGE_TTS_VOICES
from .translator import translator
from . import __version__


class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        self.setObjectName("title_bar")
        self.setFixedHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        self.title_label = QLabel(f"{translator.get('window_title')} v{__version__}")
        self.title_label.setObjectName("window_title_label")
        self.title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        layout.addWidget(self.title_label)
        layout.addStretch()

        self.min_btn = QPushButton("─")
        self.min_btn.setObjectName("btn_minimize")
        self.min_btn.setFixedSize(30, 24)
        self.min_btn.clicked.connect(self.on_minimize)

        self.max_btn = QPushButton("⬜")
        self.max_btn.setObjectName("btn_maximize")
        self.max_btn.setFixedSize(30, 24)
        self.max_btn.clicked.connect(self.on_maximize_restore)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("btn_close")
        self.close_btn.setFixedSize(30, 24)
        self.close_btn.clicked.connect(self.on_close)

        layout.addWidget(self.min_btn)
        layout.addWidget(self.max_btn)
        layout.addWidget(self.close_btn)

        self._drag_pos = None

    def on_minimize(self):
        if self._parent is not None:
            self._parent.showMinimized()

    def on_maximize_restore(self):
        if self._parent is None:
            return
        if self._parent.isMaximized():
            self._parent.showNormal()
        else:
            self._parent.showMaximized()

    def on_close(self):
        if self._parent is not None:
            self._parent.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._parent is not None:
            window = self._parent.windowHandle()
            if window is not None:
                try:
                    window.startSystemMove()
                    event.accept()
                    return
                except TypeError:
                    pass
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton and self._parent is not None:
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self._drag_pos
            self._parent.move(self._parent.pos() + delta)
            self._drag_pos = current_pos
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.on_maximize_restore()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def update_text(self):
        self.title_label.setText(translator.get('window_title'))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setWindowTitle(f"{translator.get('window_title')} v{__version__}")
        self.setMinimumSize(800, 650)
        
        self.settings = QSettings("Audio-Books-Maker", "App")
        self.output_dir = self.settings.value("output_dir", ".")
        self.current_theme = "dark"
        self.convert_thread = None
        self.selected_files = []
        
        saved_theme = self.settings.value("theme", "dark")
        self.load_stylesheet(saved_theme)
        
        self.setup_tabs()
    
    def setup_tabs(self):
        self.tab_widget = QTabWidget()
        
        self.main_tab = self.create_main_tab()
        self.settings_tab = self.create_settings_tab()
        
        self.tab_widget.addTab(self.main_tab, translator.get('tab_main'))
        self.tab_widget.addTab(self.settings_tab, translator.get('tab_settings'))
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        self.title_bar = TitleBar(self)
        container_layout.addWidget(self.title_bar)
        container_layout.addWidget(self.tab_widget)

        self.setCentralWidget(container)
    
    def create_main_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        file_section = QVBoxLayout()
        file_section.setSpacing(6)
        
        self.file_label = QLabel(translator.get('select_files'))
        file_label_layout = QHBoxLayout()
        file_label_layout.addWidget(self.file_label)
        file_label_layout.addStretch()
        file_section.addLayout(file_label_layout)
        
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(80)
        self.file_list.setMaximumHeight(120)
        file_section.addWidget(self.file_list)
        
        layout.addLayout(file_section)
        
        config_section = QGroupBox()
        config_layout = QHBoxLayout()
        
        left_layout = QFormLayout()
        left_layout.setSpacing(10)
        
        self.voice_combo = QComboBox()
        for voice_id, voice_name in EDGE_TTS_VOICES:
            self.voice_combo.addItem(voice_name, voice_id)
        
        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setMinimum(-50)
        self.rate_slider.setMaximum(50)
        self.rate_slider.setValue(5)
        self.rate_label_value = QLabel("+5%")
        
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(self.rate_slider)
        rate_layout.addWidget(self.rate_label_value)
        self.rate_slider.valueChanged.connect(self.update_rate_label)
        
        self.pitch_slider = QSlider(Qt.Horizontal)
        self.pitch_slider.setMinimum(-10)
        self.pitch_slider.setMaximum(10)
        self.pitch_slider.setValue(1)
        self.pitch_label_value = QLabel("+1Hz")
        
        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(self.pitch_slider)
        pitch_layout.addWidget(self.pitch_label_value)
        self.pitch_slider.valueChanged.connect(self.update_pitch_label)
        
        self.voice_label = QLabel(translator.get('voice_label') + ":")
        left_layout.addRow(self.voice_label, self.voice_combo)
        
        self.rate_form_label = QLabel(translator.get('rate_label') + ":")
        rate_layout.insertWidget(0, self.rate_form_label)
        left_layout.addRow(self.rate_form_label, rate_layout)
        
        self.pitch_form_label = QLabel(translator.get('pitch_label') + ":")
        pitch_layout.insertWidget(0, self.pitch_form_label)
        left_layout.addRow(self.pitch_form_label, pitch_layout)
        
        output_layout = QHBoxLayout()
        self.output_line = QLineEdit()
        self.output_line.setText(self.output_dir)
        self.output_line.setMinimumHeight(35)
        
        self.output_btn = QPushButton("📂")
        self.output_btn.setObjectName("folder_btn")
        self.output_btn.setMinimumHeight(35)
        self.output_btn.setFixedWidth(50)
        self.output_btn.clicked.connect(self.select_output_folder)
        
        output_layout.addWidget(self.output_line, 1)
        output_layout.addWidget(self.output_btn)
        
        self.output_form_label = QLabel(translator.get('output_label') + ":")
        left_layout.addRow(self.output_form_label, output_layout)
        
        self.merge_checkbox = QCheckBox(translator.get('merge_checkbox'))
        self.merge_checkbox.setChecked(True)
        left_layout.addRow("", self.merge_checkbox)
        
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        
        self.select_files_btn = QPushButton("📄 " + translator.get('select_files_btn'))
        self.select_files_btn.setObjectName("green_btn")
        self.select_files_btn.setMinimumHeight(35)
        self.select_files_btn.clicked.connect(self.select_files)
        
        self.preview_btn = QPushButton("🔊 " + translator.get('preview_btn'))
        self.preview_btn.setMinimumHeight(35)
        self.preview_btn.clicked.connect(self.preview_voice)
        
        self.start_btn = QPushButton("▶️ " + translator.get('start_btn'))
        self.start_btn.setObjectName("red_btn")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.clicked.connect(self.start_conversion)
        
        right_layout.addWidget(self.select_files_btn)
        right_layout.addWidget(self.preview_btn)
        right_layout.addStretch()
        right_layout.addWidget(self.start_btn)
        
        config_layout.addLayout(left_layout, 3)
        config_layout.addLayout(right_layout, 1)
        
        config_section.setLayout(config_layout)
        layout.addWidget(config_section)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel(translator.get('status_ready'))
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.log_toggle_btn = QPushButton(translator.get('show_log'))
        self.log_toggle_btn.setObjectName("log_toggle_btn")
        self.log_toggle_btn.setMinimumHeight(25)
        self.log_toggle_btn.clicked.connect(self.toggle_log_panel)
        self.log_toggle_btn.setVisible(False)
        layout.addWidget(self.log_toggle_btn)
        
        self.log_panel = QTextEdit()
        self.log_panel.setMaximumHeight(150)
        self.log_panel.setVisible(False)
        layout.addWidget(self.log_panel)
        
        layout.addStretch()
        
        return tab
    
    def create_settings_tab(self):
        tab = QWidget()
        
        grid_layout = QGridLayout(tab)
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(20, 20, 20, 20)
        
        self.theme_group = QGroupBox(translator.get('settings_theme'))
        theme_layout = QVBoxLayout()
        
        self.dark_radio = QRadioButton(translator.get('theme_dark'))
        self.light_radio = QRadioButton(translator.get('theme_light'))
        
        saved_theme = self.settings.value("theme", "dark")
        self.dark_radio.setChecked(saved_theme == 'dark')
        self.light_radio.setChecked(saved_theme == 'light')
        
        self.dark_radio.clicked.connect(lambda: self.change_theme('dark'))
        self.light_radio.clicked.connect(lambda: self.change_theme('light'))
        
        theme_layout.addWidget(self.dark_radio)
        theme_layout.addWidget(self.light_radio)
        self.theme_group.setLayout(theme_layout)
        grid_layout.addWidget(self.theme_group, 0, 0)
        
        self.language_group = QGroupBox(translator.get('settings_language'))
        language_layout = QVBoxLayout()
        
        self.english_radio = QRadioButton(translator.get('language_english'))
        self.chinese_radio = QRadioButton(translator.get('language_chinese'))
        
        current_lang = translator.current_lang
        self.english_radio.setChecked(current_lang == 'en')
        self.chinese_radio.setChecked(current_lang == 'zh')
        
        self.english_radio.clicked.connect(lambda: self.change_language('en'))
        self.chinese_radio.clicked.connect(lambda: self.change_language('zh'))
        
        language_layout.addWidget(self.english_radio)
        language_layout.addWidget(self.chinese_radio)
        self.language_group.setLayout(language_layout)
        grid_layout.addWidget(self.language_group, 0, 1)
        
        self.concurrency_group = QGroupBox(translator.get('settings_concurrency'))
        concurrency_layout = QFormLayout()
        
        self.concurrency_slider = QSlider(Qt.Horizontal)
        self.concurrency_slider.setMinimum(1)
        self.concurrency_slider.setMaximum(10)
        self.concurrency_slider.setValue(int(self.settings.value("concurrency", 1)))
        self.concurrency_slider.valueChanged.connect(self.save_concurrency_settings)
        
        self.concurrency_label_value = QLabel(str(self.concurrency_slider.value()))
        
        concurrency_row = QHBoxLayout()
        concurrency_row.addWidget(self.concurrency_slider)
        concurrency_row.addWidget(self.concurrency_label_value)
        
        self.delay_slider = QSlider(Qt.Horizontal)
        self.delay_slider.setMinimum(0)
        self.delay_slider.setMaximum(50)  # 0.0 - 5.0
        self.delay_slider.setValue(int(float(self.settings.value("delay", 1.0)) * 10))
        self.delay_slider.valueChanged.connect(self.save_concurrency_settings)
        
        self.delay_label_value = QLabel(f"{self.delay_slider.value() / 10:.1f}s")
        
        delay_row = QHBoxLayout()
        delay_row.addWidget(self.delay_slider)
        delay_row.addWidget(self.delay_label_value)
        
        self.concurrency_label_form = QLabel(translator.get('concurrency_label') + ":")
        concurrency_form_layout = QHBoxLayout()
        concurrency_form_layout.addWidget(self.concurrency_slider)
        concurrency_form_layout.addWidget(self.concurrency_label_value)
        concurrency_layout.addRow(self.concurrency_label_form, concurrency_form_layout)
        
        self.delay_label_form = QLabel(translator.get('delay_label') + ":")
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(self.delay_slider)
        delay_layout.addWidget(self.delay_label_value)
        concurrency_layout.addRow(self.delay_label_form, delay_layout)
        
        self.concurrency_group.setLayout(concurrency_layout)
        grid_layout.addWidget(self.concurrency_group, 1, 0)
        
        self.about_group = QGroupBox(translator.get('settings_about'))
        about_main_layout = QHBoxLayout()
        
        about_left_layout = QVBoxLayout()
        self.about_text = QTextEdit()
        self.about_text.setReadOnly(True)
        self.about_text.setPlainText(
            f"{translator.get('about_description')}\n\n"
            f"{translator.get('about_author')}\n"
            f"{translator.get('about_version')}: v{__version__}"
        )
        self.about_text.setMaximumHeight(100)
        about_left_layout.addWidget(self.about_text)
        
        about_right_layout = QVBoxLayout()
        base_path = self.get_base_path()
        author_png_path = os.path.join(base_path, 'author.png')
        author_pixmap = QPixmap(author_png_path)
        if not author_pixmap.isNull():
            author_label = QLabel()
            author_label.setPixmap(author_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            about_right_layout.addWidget(author_label)
        
        about_main_layout.addLayout(about_left_layout, 3)
        about_main_layout.addLayout(about_right_layout, 1)
        
        self.about_group.setLayout(about_main_layout)
        grid_layout.addWidget(self.about_group, 2, 0, 1, 2)
        
        grid_layout.setRowStretch(3, 1)
        
        return tab
    
    def update_rate_label(self, value):
        if value >= 0:
            self.rate_label_value.setText(f"+{value}%")
        else:
            self.rate_label_value.setText(f"{value}%")
    
    def update_pitch_label(self, value):
        if value >= 0:
            self.pitch_label_value.setText(f"+{value}Hz")
        else:
            self.pitch_label_value.setText(f"{value}Hz")
    
    def preview_voice(self):
        voice = self.voice_combo.currentData()
        rate = f"+{self.rate_slider.value()}%" if self.rate_slider.value() >= 0 else f"{self.rate_slider.value()}%"
        pitch = f"+{self.pitch_slider.value()}Hz" if self.pitch_slider.value() >= 0 else f"{self.pitch_slider.value()}Hz"
        
        self.preview_btn.setEnabled(False)
        self.set_status(translator.get('status_preview_generating'))
        
        preview_text = translator.get('preview_text')
        self.preview_thread = PreviewThread(voice, rate, pitch, preview_text)
        self.preview_thread.finished.connect(self.on_preview_finished)
        self.preview_thread.error.connect(self.on_preview_error)
        self.preview_thread.start()
    
    def on_preview_finished(self):
        self.preview_btn.setEnabled(True)
        self.set_status(translator.get('status_ready'))
    
    def on_preview_error(self, error):
        self.preview_btn.setEnabled(True)
        self.set_status(f"{translator.get('status_preview_failed')}{error}", is_error=True)
    
    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            translator.get('select_files_btn'),
            ".",
            "Ebooks (*.epub *.txt *.pdf);;All Files (*)"
        )
        if files:
            self.selected_files = files
            self.file_list.clear()
            for f in files:
                self.file_list.addItem(os.path.basename(f))
    
    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, translator.get('output_btn'))
        if folder:
            self.output_dir = folder
            self.output_line.setText(folder)
            self.settings.setValue("output_dir", folder)
    
    def start_conversion(self):
        if not self.selected_files:
            self.set_status(translator.get('select_files_first'), is_error=True)
            return
        
        if not self.output_dir or not os.path.isdir(self.output_dir):
            self.set_status(translator.get('select_output_first'), is_error=True)
            return
        
        voice = self.voice_combo.currentData()
        rate = f"+{self.rate_slider.value()}%" if self.rate_slider.value() >= 0 else f"{self.rate_slider.value()}%"
        pitch = f"+{self.pitch_slider.value()}Hz" if self.pitch_slider.value() >= 0 else f"{self.pitch_slider.value()}Hz"
        merge = self.merge_checkbox.isChecked()
        
        concurrency = int(self.settings.value("concurrency", 1))
        delay = float(self.settings.value("delay", 1.0))
        
        self.convert_thread = ConvertThread(
            self.selected_files,
            self.output_dir,
            voice,
            rate,
            pitch,
            merge,
            concurrency,
            delay
        )
        
        self.convert_thread.progress.connect(self.progress_bar.setValue)
        self.convert_thread.status.connect(self.set_status)
        self.convert_thread.log.connect(self.append_log)
        self.convert_thread.finished.connect(self.on_conversion_finished)
        self.convert_thread.error.connect(self.on_conversion_error)
        
        self.convert_thread.start()
        
        self.start_btn.setEnabled(False)
        self.select_files_btn.setEnabled(False)
        self.log_toggle_btn.setVisible(True)
    
    def stop_conversion(self):
        if self.convert_thread and self.convert_thread.isRunning():
            self.convert_thread.stop()
            self.set_status("Stopping...")
    
    def append_log(self, text):
        self.log_panel.append(text)
    
    def toggle_log_panel(self):
        if self.log_panel.isVisible():
            self.log_panel.setVisible(False)
            self.log_toggle_btn.setText("📋 " + translator.get('show_log'))
        else:
            self.log_panel.setVisible(True)
            self.log_toggle_btn.setText("📋 " + translator.get('hide_log'))
    
    def on_conversion_finished(self, message):
        self.start_btn.setEnabled(True)
        self.select_files_btn.setEnabled(True)
        self.set_status(message)
        self.progress_bar.setValue(100)
    
    def on_conversion_error(self, error):
        self.start_btn.setEnabled(True)
        self.select_files_btn.setEnabled(True)
        self.set_status(f"{translator.get('status_error')}{error}", is_error=True)
    
    def set_status(self, message, is_error=False):
        self.status_label.setText(message)
        if is_error:
            if self.current_theme == "light":
                self.status_label.setStyleSheet("QLabel#status_label { color: #e74c3c; font-size: 14px; font-weight: bold; padding: 5px; }")
            else:
                self.status_label.setStyleSheet("QLabel#status_label { color: #e74c3c; font-size: 14px; font-weight: bold; padding: 5px; }")
        else:
            if self.current_theme == "light":
                self.status_label.setStyleSheet("QLabel#status_label { color: #2980b9; font-size: 14px; font-weight: bold; padding: 5px; }")
            else:
                self.status_label.setStyleSheet("QLabel#status_label { color: #3498db; font-size: 14px; font-weight: bold; padding: 5px; }")
    
    def change_theme(self, theme):
        self.load_stylesheet(theme)
        
        if hasattr(self, 'dark_radio') and hasattr(self, 'light_radio'):
            self.dark_radio.setChecked(theme == 'dark')
            self.light_radio.setChecked(theme == 'light')
    
    def change_language(self, lang_code):
        if translator.set_language(lang_code):
            self.tab_widget.setTabText(0, translator.get('tab_main'))
            self.tab_widget.setTabText(1, translator.get('tab_settings'))
            self.update_ui_text()
            if hasattr(self, 'title_bar'):
                self.title_bar.update_text()
    
    def update_ui_text(self):
        self.setWindowTitle(f"{translator.get('window_title')} v{__version__}")
        
        for widget in self.findChildren(QLabel):
            if widget.objectName() == "title_label":
                widget.setText(translator.get('title_label'))
        
        self.select_files_btn.setText("📄 " + translator.get('select_files_btn'))
        self.output_btn.setToolTip(translator.get('folder_btn'))
        self.merge_checkbox.setText(translator.get('merge_checkbox'))
        self.preview_btn.setText("🔊 " + translator.get('preview_btn'))
        self.start_btn.setText("▶️ " + translator.get('start_btn'))
        
        if hasattr(self, 'voice_label'):
            self.voice_label.setText(translator.get('voice_label') + ":")
        if hasattr(self, 'rate_form_label'):
            self.rate_form_label.setText(translator.get('rate_label') + ":")
        if hasattr(self, 'pitch_form_label'):
            self.pitch_form_label.setText(translator.get('pitch_label') + ":")
        if hasattr(self, 'output_form_label'):
            self.output_form_label.setText(translator.get('output_label') + ":")
        
        if hasattr(self, 'file_label'):
            self.file_label.setText(translator.get('select_files'))
        
        if hasattr(self, 'theme_group'):
            self.theme_group.setTitle(translator.get('settings_theme'))
            self.dark_radio.setText(translator.get('theme_dark'))
            self.light_radio.setText(translator.get('theme_light'))
        
        if hasattr(self, 'language_group'):
            self.language_group.setTitle(translator.get('settings_language'))
            self.english_radio.setText(translator.get('language_english'))
            self.chinese_radio.setText(translator.get('language_chinese'))
        
        if hasattr(self, 'about_group'):
            self.about_group.setTitle(translator.get('settings_about'))
            self.about_text.setPlainText(
                f"{translator.get('about_description')}\n\n"
                f"{translator.get('about_author')}\n"
                f"{translator.get('about_version')}: v{__version__}"
            )
        
        if hasattr(self, 'concurrency_group'):
            self.concurrency_group.setTitle(translator.get('settings_concurrency'))
            if hasattr(self, 'concurrency_label_form'):
                self.concurrency_label_form.setText(translator.get('concurrency_label') + ":")
            self.concurrency_label_value.setText(str(self.concurrency_slider.value()))
            if hasattr(self, 'delay_label_form'):
                self.delay_label_form.setText(translator.get('delay_label') + ":")
            self.delay_label_value.setText(f"{self.delay_slider.value() / 10.0:.1f}s")
    
    def save_concurrency_settings(self):
        concurrency = self.concurrency_slider.value()
        delay = self.delay_slider.value() / 10.0
        self.settings.setValue("concurrency", concurrency)
        self.settings.setValue("delay", delay)
        self.concurrency_label_value.setText(str(concurrency))
        self.delay_label_value.setText(f"{delay:.1f}s")
    
    def get_base_path(self):
        import sys
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                return sys._MEIPASS
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def load_stylesheet(self, theme='dark'):
        if theme == 'dark':
            style_file = 'style.qss'
        else:
            style_file = 'style_light.qss'
        
        self.current_theme = theme
        
        base_path = self.get_base_path()
        style_path = os.path.join(base_path, 'app', style_file)
        
        if not os.path.exists(style_path):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            style_path = os.path.join(current_dir, style_file)
        
        if os.path.exists(style_path):
            with open(style_path, 'r') as f:
                self.setStyleSheet(f.read())
        
        self.settings.setValue("theme", theme)