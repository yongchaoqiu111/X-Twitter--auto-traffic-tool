"""
自动发帖Tab界面 (重构版)
"""
import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QGroupBox, QFormLayout, QLineEdit, QMessageBox, QFileDialog, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from modules.auto_post import XAutoPost
from modules.auto_post_worker import AutoPostWorker
from modules.i18n_manager import I18nManager

class AutoPostTab(QWidget):
    def __init__(self, data_dir):
        super().__init__()
        self.data_dir = data_dir
        self.i18n = I18nManager()
        self.auto_post = XAutoPost(data_dir)
        self.worker = None
        self.images_dir = r'D:\weibo\X\1'
        self.texts_dir = r'D:\weibo\X\2'
        self.params_file = os.path.join(data_dir, 'auto-post-params.json')
        self.init_ui()
        self.init_ui_complete()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 标题
        self.title = QLabel(self.i18n.t("x_post_title"))
        self.title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        main_layout.addWidget(self.title)
        
        # 说明卡片
        self.info_group = QGroupBox(self.i18n.t("x_post_guide_group"))
        self.info_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        info_layout = QVBoxLayout()
        self.info_text = QLabel(self.i18n.t("x_post_guide_text").format(self.images_dir, self.texts_dir))
        self.info_text.setWordWrap(True)
        self.info_text.setStyleSheet("line-height: 150%; color: #555;")
        info_layout.addWidget(self.info_text)
        self.info_group.setLayout(info_layout)
        main_layout.addWidget(self.info_group)
        
        # 文件选择区
        self.file_group = QGroupBox(self.i18n.t("file_selection_group"))
        file_layout = QVBoxLayout()
        
        # 媒体文件选择
        img_row = QHBoxLayout()
        img_row.addWidget(QLabel(self.i18n.t("media_file_label")))
        self.img_combo = QComboBox()
        self.img_combo.setMinimumWidth(300)
        img_row.addWidget(self.img_combo)
        self.btn_refresh_img = QPushButton(self.i18n.t("btn_refresh"))
        self.btn_refresh_img.clicked.connect(lambda: self.refresh_files('img'))
        img_row.addWidget(self.btn_refresh_img)
        file_layout.addLayout(img_row)
        
        # 文案文件选择
        text_row = QHBoxLayout()
        text_row.addWidget(QLabel(self.i18n.t("text_file_label")))
        self.text_combo = QComboBox()
        self.text_combo.setMinimumWidth(300)
        text_row.addWidget(self.text_combo)
        self.btn_refresh_text = QPushButton(self.i18n.t("btn_refresh"))
        self.btn_refresh_text.clicked.connect(lambda: self.refresh_files('text'))
        text_row.addWidget(self.btn_refresh_text)
        file_layout.addLayout(text_row)
        
        self.file_group.setLayout(file_layout)
        main_layout.addWidget(self.file_group)
        
        # 状态显示
        self.control_group = QGroupBox(self.i18n.t("x_post_control_group"))
        control_layout = QVBoxLayout()
        
        self.status_label = QLabel(self.i18n.t("status_not_started"))
        control_layout.addWidget(self.status_label)
        
        self.progress_label = QLabel(self.i18n.t("progress_format").format(0, 0))
        control_layout.addWidget(self.progress_label)
        
        self.message_label = QLabel("")
        self.message_label.setStyleSheet("color: green; padding: 10px;")
        control_layout.addWidget(self.message_label)
        
        self.control_group.setLayout(control_layout)
        main_layout.addWidget(self.control_group)
        
        # 启动按钮
        self.btn_start = QPushButton(self.i18n.t("btn_start_x_post"))
        self.btn_start.setMinimumHeight(50)
        self.btn_start.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
        """)
        self.btn_start.clicked.connect(self.start_posting)
        main_layout.addWidget(self.btn_start)
        
        main_layout.addStretch()
        
        # 保存线程引用，防止被垃圾回收
        self.thread = None
    
    def init_ui_complete(self):
        """UI初始化完成后调用"""
        # 初始刷新文件列表
        self.refresh_files('img')
        self.refresh_files('text')
    
    def refresh_files(self, type_str):
        """刷新文件列表"""
        if type_str == 'img':
            try:
                files = sorted([f for f in os.listdir(self.images_dir) 
                               if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.webp'))])
                self.img_combo.clear()
                self.img_combo.addItems(files)
                self.show_message(self.i18n.t("refresh_media_success").format(len(files)), "green")
            except Exception as e:
                self.show_message(self.i18n.t("refresh_failed").format(e), "red")
        else:
            try:
                files = sorted([f for f in os.listdir(self.texts_dir) 
                               if f.lower().endswith('.txt')])
                self.text_combo.clear()
                self.text_combo.addItems(files)
                self.show_message(self.i18n.t("refresh_text_success").format(len(files)), "green")
            except Exception as e:
                self.show_message(self.i18n.t("refresh_failed").format(e), "red")
    
    def start_posting(self):
        # 获取当前选择的文件
        img_file = self.img_combo.currentText()
        text_file = self.text_combo.currentText()
        
        if not img_file or not text_file:
            QMessageBox.warning(self, self.i18n.t("warning"), self.i18n.t("msg_select_file_warning"))
            return
        
        reply = QMessageBox.question(
            self, self.i18n.t("confirm"), 
            self.i18n.t("confirm_start_post").format(img_file, text_file),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.btn_start.setEnabled(False)
        self.status_label.setText(self.i18n.t("status_running"))
        self.status_label.setStyleSheet("color: green;")
        
        # 传递选中的文件
        img_path = os.path.join(self.images_dir, img_file)
        text_path = os.path.join(self.texts_dir, text_file)
        self.worker = AutoPostWorker(self.auto_post, self.images_dir, self.texts_dir, img_path, text_path)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.log.connect(self.on_log)
        
        # 启动工作线程
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.start_posting)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()
    
    def on_progress(self, current, total, message):
        self.progress_label.setText(self.i18n.t("progress_format").format(current, total))
        self.show_message(message, "blue")
    
    def on_log(self, message):
        current_text = self.message_label.text()
        if current_text and current_text.startswith(self.i18n.t("log_prefix")):
            self.message_label.setText(current_text + "\n" + message)
        else:
            self.message_label.setText(self.i18n.t("log_prefix") + "\n" + message)
    
    def on_finished(self, success, message, count):
        self.btn_start.setEnabled(True)
        if success:
            self.status_label.setText(self.i18n.t("status_completed").format(count))
            self.status_label.setStyleSheet("color: blue;")
            self.show_message(message, "green")
        else:
            self.status_label.setText(self.i18n.t("status_failed"))
            self.status_label.setStyleSheet("color: red;")
            self.show_message(self.i18n.t("error_format").format(message), "red")
    
    def show_message(self, text, color):
        self.message_label.setText(text)
        self.message_label.setStyleSheet(f"color: {color}; padding: 10px;")
    
    def update_language(self):
        """更新界面语言"""
        self.title.setText(self.i18n.t("x_post_title"))
        self.info_group.setTitle(self.i18n.t("x_post_guide_group"))
        self.info_text.setText(self.i18n.t("x_post_guide_text").format(self.images_dir, self.texts_dir))
        self.file_group.setTitle(self.i18n.t("file_selection_group"))
        self.control_group.setTitle(self.i18n.t("x_post_control_group"))
        self.btn_start.setText(self.i18n.t("btn_start_x_post"))
