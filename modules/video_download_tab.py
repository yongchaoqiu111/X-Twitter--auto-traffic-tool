"""
X 视频下载模块
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGroupBox, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import os
import sys
import subprocess
import json
from modules.i18n_manager import I18nManager


class DownloadWorker(QThread):
    """下载工作线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, url, download_dir, cookie_file):
        super().__init__()
        self.url = url
        self.download_dir = download_dir
        self.cookie_file = cookie_file
    
    def run(self):
        try:
            import yt_dlp
            import time
            
            self.progress.emit("正在解析视频链接...")
            
            # yt-dlp 配置
            ydl_opts = {
                'outtmpl': os.path.join(self.download_dir, 'x_video_%(id)s.%(ext)s'),
                'format': 'best',  # 使用最佳单一格式，避免需要 ffmpeg 合并
                'progress_hooks': [self._progress_hook],
                'quiet': False,
                'no_warnings': False,
            }
            
            self.progress.emit("正在下载视频...")
            
            # 执行下载
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                
                if info:
                    # 获取文件路径
                    filename = ydl.prepare_filename(info)
                    if os.path.exists(filename):
                        self.finished.emit(True, filename)
                    else:
                        self.finished.emit(False, "下载完成但找不到文件")
                else:
                    self.finished.emit(False, "无法获取视频信息")
                    
        except Exception as e:
            error_msg = str(e)
            if 'Private' in error_msg or 'private' in error_msg:
                error_msg = "视频是私密的或需要登录，请确保 Cookie 有效"
            elif 'unavailable' in error_msg.lower():
                error_msg = "视频不可用或已被删除"
            self.finished.emit(False, error_msg)
    
    def _progress_hook(self, d):
        """进度回调"""
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            
            if total > 0:
                percent = downloaded / total * 100
                speed = d.get('speed', 0)
                
                if speed:
                    speed_mb = speed / 1024 / 1024
                    self.progress.emit(f"正在下载: {percent:.1f}% ({speed_mb:.1f} MB/s)")
                else:
                    self.progress.emit(f"正在下载: {percent:.1f}%")
            else:
                self.progress.emit("正在下载...")
        elif d['status'] == 'finished':
            self.progress.emit("下载完成，正在合并文件...")


class VideoDownloadTab(QWidget):
    """X 视频下载 Tab 页面"""
    
    def __init__(self, data_dir):
        super().__init__()
        self.data_dir = data_dir
        self.i18n = I18nManager()
        self.download_dir = os.path.join(data_dir, "downloads")
        self.cookie_file = os.path.join(data_dir, "x_cookie.txt")
        os.makedirs(self.download_dir, exist_ok=True)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel(self.i18n.t("video_download_title"))
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 视频链接输入区域
        url_group = QGroupBox(self.i18n.t("video_url_label"))
        url_group.setFont(QFont("Microsoft YaHei", 10))
        url_layout = QVBoxLayout(url_group)
        
        url_input_layout = QHBoxLayout()
        url_label = QLabel(self.i18n.t("video_url_label"))
        url_label.setFont(QFont("Microsoft YaHei", 10))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(self.i18n.t("video_url_placeholder"))
        self.url_input.setFont(QFont("Microsoft YaHei", 10))
        
        url_input_layout.addWidget(url_label)
        url_input_layout.addWidget(self.url_input)
        url_group.setLayout(url_layout)
        url_layout.addLayout(url_input_layout)
        
        layout.addWidget(url_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.download_btn = QPushButton(" " + self.i18n.t("btn_download_video"))
        self.download_btn.setFixedSize(150, 40)
        self.download_btn.setFont(QFont("Microsoft YaHei", 10))
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #1DA1F2;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0d8bd9;
            }
            QPushButton:pressed {
                background-color: #0c7abf;
            }
        """)
        self.download_btn.clicked.connect(self.start_download)
        
        self.open_folder_btn = QPushButton("📂 " + self.i18n.t("btn_open_folder"))
        self.open_folder_btn.setFixedSize(150, 40)
        self.open_folder_btn.setFont(QFont("Microsoft YaHei", 10))
        self.open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.open_folder_btn.clicked.connect(self.open_download_folder)
        
        self.open_x_btn = QPushButton("🌐 " + self.i18n.t("btn_open_x"))
        self.open_x_btn.setFixedSize(150, 40)
        self.open_x_btn.setFont(QFont("Microsoft YaHei", 10))
        self.open_x_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.open_x_btn.clicked.connect(self.open_x_with_cookie)
        
        button_layout.addWidget(self.download_btn)
        button_layout.addWidget(self.open_folder_btn)
        button_layout.addWidget(self.open_x_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 使用说明
        usage_group = QGroupBox(self.i18n.t("usage_instructions_group"))
        usage_group.setFont(QFont("Microsoft YaHei", 10))
        usage_layout = QVBoxLayout(usage_group)
        
        usage_text = QLabel(self.i18n.t("video_usage_text"))
        usage_text.setFont(QFont("Microsoft YaHei", 9))
        usage_text.setWordWrap(True)
        usage_layout.addWidget(usage_text)
        
        layout.addWidget(usage_group)
        
        # 状态标签
        self.status_label = QLabel(self.i18n.t("status_ready"))
        self.status_label.setFont(QFont("Microsoft YaHei", 10))
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def start_download(self):
        """开始下载视频"""
        url = self.url_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, self.i18n.t("warning"), self.i18n.t("msg_enter_url"))
            return
        
        if not os.path.exists(self.cookie_file):
            QMessageBox.warning(self, self.i18n.t("warning"), self.i18n.t("msg_save_cookie_first"))
            return
        
        # 禁用按钮
        self.download_btn.setEnabled(False)
        self.status_label.setText(self.i18n.t("status_downloading"))
        
        # 创建下载线程
        self.worker = DownloadWorker(url, self.download_dir, self.cookie_file)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
    
    def on_progress(self, message):
        """下载进度更新"""
        self.status_label.setText(f"{self.i18n.t('current_status')} {message}")
    
    def on_finished(self, success, message):
        """下载完成"""
        self.download_btn.setEnabled(True)
        
        if success:
            self.status_label.setText(self.i18n.t("status_download_complete"))
            QMessageBox.information(self, self.i18n.t("completed"), self.i18n.t("download_success").format(message))
        else:
            self.status_label.setText(self.i18n.t("status_download_failed"))
            QMessageBox.critical(self, self.i18n.t("failed"), self.i18n.t("download_failed").format(message))
    
    def open_download_folder(self):
        """打开下载文件夹"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir, exist_ok=True)
        
        # Windows 打开文件夹
        if sys.platform == 'win32':
            os.startfile(self.download_dir)
        else:
            subprocess.run(['open', self.download_dir])
    
    def open_x_with_cookie(self):
        """携带 Cookie 打开 X"""
        if not os.path.exists(self.cookie_file):
            QMessageBox.warning(self, self.i18n.t("warning"), self.i18n.t("msg_save_cookie_first"))
            return
        
        self.status_label.setText(self.i18n.t("opening_x"))
        
        try:
            # 这里可以调用登录管理中的加载 Cookie 功能
            # 暂时直接打开浏览器
            import subprocess
            subprocess.Popen(['start', 'https://x.com'], shell=True)
            self.status_label.setText(self.i18n.t("x_opened"))
        except Exception as e:
            self.status_label.setText(self.i18n.t("open_failed").format(e))
    
    def update_language(self):
        """更新语言"""
        # 按钮文本
        self.download_btn.setText(" " + self.i18n.t("btn_download_video"))
        self.open_folder_btn.setText("📂 " + self.i18n.t("btn_open_folder"))
        self.open_x_btn.setText("🌐 " + self.i18n.t("btn_open_x"))
        
        # 状态标签
        if hasattr(self, 'worker') and self.worker.isRunning():
            pass  # 正在下载时不更新状态
        else:
            self.status_label.setText(self.i18n.t("status_ready"))
        
        # 更新所有标题和标签
        for child in self.findChildren(QLabel):
            text = child.text()
            if text.startswith("X ") and ("视频" in text or "Video" in text):
                child.setText(self.i18n.t("video_download_title"))
            elif "Video URL" in text or "视频链接" in text:
                child.setText(self.i18n.t("video_url_label"))
        
        # 更新 GroupBox 标题
        for child in self.findChildren(QGroupBox):
            title = child.title()
            if "Instructions" in title or "使用说明" in title:
                child.setTitle(self.i18n.t("usage_instructions_group"))
            elif "Video URL" in title or "视频链接" in title:
                child.setTitle(self.i18n.t("video_url_label"))
        
        # 更新输入框占位符
        self.url_input.setPlaceholderText(self.i18n.t("video_url_placeholder"))
        
        # 更新使用说明文本
        for child in self.findChildren(QLabel):
            if "1. 复制" in child.text() or "1. Copy" in child.text():
                child.setText(self.i18n.t("video_usage_text"))
                break
