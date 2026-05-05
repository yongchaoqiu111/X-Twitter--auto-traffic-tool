"""
视频合成工具 - 背景视频 + 音频 + 字幕
"""
import os
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, 
                             QMessageBox, QGroupBox, QTextEdit, QComboBox,
                             QSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


class SubtitleWorker(QThread):
    """视频合成工作线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, video_path, audio_path, subtitle_path, output_path, font_size=24):
        super().__init__()
        self.video_path = video_path
        self.audio_path = audio_path
        self.subtitle_path = subtitle_path
        self.output_path = output_path
        self.font_size = font_size
    
    def run(self):
        try:
            import subprocess
            
            self.progress.emit("正在检查文件...")
            
            # 检查输入文件
            if not os.path.exists(self.video_path):
                self.finished.emit(False, "视频文件不存在")
                return
            
            if not os.path.exists(self.audio_path):
                self.finished.emit(False, "音频文件不存在")
                return
            
            if not os.path.exists(self.subtitle_path):
                self.finished.emit(False, "字幕文件不存在")
                return
            
            # 如果字幕是 TXT 格式，转换为 SRT
            srt_path = self.subtitle_path
            if self.subtitle_path.lower().endswith('.txt'):
                self.progress.emit("正在转换 TXT 为 SRT 格式...")
                srt_path = self.convert_txt_to_srt(self.subtitle_path)
            
            self.progress.emit("正在合成视频（背景+音频+字幕）...")
            
            # 使用 FFmpeg 合成视频
            # 1. 视频循环播放
            # 2. 替换音频
            # 3. 添加字幕
            srt_path_escaped = srt_path.replace('\\', '/')
            
            # 获取音频时长
            self.progress.emit("正在获取音频时长...")
            duration_cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                self.audio_path
            ]
            
            result = subprocess.run(duration_cmd, capture_output=True, text=True, encoding='utf-8')
            audio_duration = float(result.stdout.strip())
            
            self.progress.emit(f"音频时长: {audio_duration:.1f} 秒")
            
            # FFmpeg 命令：视频循环 + 音频替换 + 字幕
            cmd = [
                'ffmpeg',
                '-stream_loop', '-1',  # 视频无限循环
                '-i', self.video_path,
                '-i', self.audio_path,
                '-vf', f"subtitles='{srt_path_escaped}':force_style='FontName=Microsoft YaHei,FontSize={self.font_size},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1'",
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-t', str(audio_duration),  # 输出时长等于音频时长
                '-shortest',
                '-y',
                self.output_path
            ]
            
            self.progress.emit("开始合成...")
            
            # 执行 FFmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8'
            )
            
            # 读取输出
            for line in process.stdout:
                if 'time=' in line:
                    self.progress.emit(f"处理中: {line.strip()}")
            
            process.wait()
            
            if process.returncode == 0:
                self.finished.emit(True, self.output_path)
            else:
                self.finished.emit(False, f"FFmpeg 错误: {process.returncode}")
                
        except FileNotFoundError:
            self.finished.emit(False, "未找到 FFmpeg，请先安装 FFmpeg\n下载地址: https://ffmpeg.org/download.html")
        except Exception as e:
            self.finished.emit(False, str(e))
    
    def convert_txt_to_srt(self, txt_path):
        """将纯文本字幕转换为 SRT 格式"""
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        srt_lines = []
        index = 1
        
        # 简单转换：每行字幕持续 3 秒
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            start_time = i * 3
            end_time = start_time + 3
            
            start_str = self.format_srt_time(start_time)
            end_str = self.format_srt_time(end_time)
            
            srt_lines.append(str(index))
            srt_lines.append(f"{start_str} --> {end_str}")
            srt_lines.append(line)
            srt_lines.append("")
            
            index += 1
        
        # 保存为 SRT 文件
        srt_path = txt_path.replace('.txt', '.srt')
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_lines))
        
        return srt_path
    
    def format_srt_time(self, seconds):
        """将秒数转换为 SRT 时间格式 (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class SubtitleTab(QWidget):
    """视频字幕 Tab"""
    
    def __init__(self, data_dir):
        super().__init__()
        self.data_dir = data_dir
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("视频字幕工具")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 视频文件选择
        video_group = QGroupBox("1. 选择视频文件")
        video_layout = QHBoxLayout()
        
        self.video_input = QLineEdit()
        self.video_input.setPlaceholderText("选择视频文件 (MP4, AVI, MKV...)")
        self.video_input.setReadOnly(True)
        
        video_btn = QPushButton("浏览...")
        video_btn.setFixedWidth(100)
        video_btn.setStyleSheet("""
            QPushButton {
                background-color: #1DA1F2;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #0d8bd9;
            }
        """)
        video_btn.clicked.connect(self.select_video)
        
        video_layout.addWidget(self.video_input)
        video_layout.addWidget(video_btn)
        video_group.setLayout(video_layout)
        layout.addWidget(video_group)
        
        # 字幕文件选择
        subtitle_group = QGroupBox("2. 选择字幕文件")
        subtitle_layout = QHBoxLayout()
        
        self.subtitle_input = QLineEdit()
        self.subtitle_input.setPlaceholderText("选择字幕文件 (SRT 或 TXT)")
        self.subtitle_input.setReadOnly(True)
        
        subtitle_btn = QPushButton("浏览...")
        subtitle_btn.setFixedWidth(100)
        subtitle_btn.setStyleSheet("""
            QPushButton {
                background-color: #1DA1F2;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #0d8bd9;
            }
        """)
        subtitle_btn.clicked.connect(self.select_subtitle)
        
        subtitle_layout.addWidget(self.subtitle_input)
        subtitle_layout.addWidget(subtitle_btn)
        subtitle_group.setLayout(subtitle_layout)
        layout.addWidget(subtitle_group)
        
        # 字幕样式设置
        style_group = QGroupBox("3. 字幕样式设置")
        style_layout = QVBoxLayout()
        
        # 字体大小
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("字体大小:"))
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems(['16', '20', '24', '28', '32', '36', '40'])
        self.font_size_combo.setCurrentText('24')
        font_size_layout.addWidget(self.font_size_combo)
        font_size_layout.addStretch()
        style_layout.addLayout(font_size_layout)
        
        # 字体颜色
        font_color_layout = QHBoxLayout()
        font_color_layout.addWidget(QLabel("字体颜色:"))
        self.font_color_combo = QComboBox()
        self.font_color_combo.addItems(['白色', '黄色', '红色', '绿色'])
        font_color_layout.addWidget(self.font_color_combo)
        font_color_layout.addStretch()
        style_layout.addLayout(font_color_layout)
        
        style_group.setLayout(style_layout)
        layout.addWidget(style_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.start_btn = QPushButton("开始添加字幕")
        self.start_btn.setFixedHeight(45)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.start_btn.clicked.connect(self.start_processing)
        btn_layout.addWidget(self.start_btn)
        
        self.open_folder_btn = QPushButton("打开输出文件夹")
        self.open_folder_btn.setFixedHeight(45)
        self.open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        btn_layout.addWidget(self.open_folder_btn)
        
        layout.addLayout(btn_layout)
        
        # 使用说明
        help_group = QGroupBox("使用说明")
        help_layout = QVBoxLayout()
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(150)
        help_text.setText("""
1. 选择要添加字幕的视频文件
2. 选择字幕文件（支持 SRT 或 TXT 格式）
   - SRT 格式：包含时间轴的标准字幕格式
   - TXT 格式：纯文本，每行自动分配 3 秒显示时间
3. 设置字幕样式（字体大小、颜色）
4. 点击"开始添加字幕"按钮
5. 等待处理完成，输出文件保存在原视频同目录

注意：需要先安装 FFmpeg
下载地址: https://ffmpeg.org/download.html
        """)
        help_layout.addWidget(help_text)
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def select_video(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.wmv);;所有文件 (*)"
        )
        if file_path:
            self.video_input.setText(file_path)
    
    def select_subtitle(self):
        """选择字幕文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择字幕文件",
            "",
            "字幕文件 (*.srt *.txt);;所有文件 (*)"
        )
        if file_path:
            self.subtitle_input.setText(file_path)
    
    def start_processing(self):
        """开始处理"""
        video_path = self.video_input.text()
        subtitle_path = self.subtitle_input.text()
        
        if not video_path or not subtitle_path:
            QMessageBox.warning(self, "警告", "请选择视频文件和字幕文件")
            return
        
        # 生成输出文件名
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(video_dir, f"{video_name}_with_subtitles.mp4")
        
        # 获取样式设置
        font_size = int(self.font_size_combo.currentText())
        font_color_map = {
            '白色': 'white',
            '黄色': 'yellow',
            '红色': 'red',
            '绿色': 'green'
        }
        font_color = font_color_map[self.font_color_combo.currentText()]
        
        # 禁用按钮
        self.start_btn.setEnabled(False)
        self.status_label.setText("正在处理...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #1DA1F2;
                padding: 10px;
                background-color: #e7f3ff;
                border-radius: 5px;
            }
        """)
        
        # 启动工作线程
        self.worker = SubtitleWorker(video_path, subtitle_path, output_path, font_size, font_color)
        self.worker.progress.connect(self.update_status)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
    
    def update_status(self, message):
        """更新状态"""
        self.status_label.setText(message)
    
    def on_finished(self, success, message):
        """处理完成"""
        self.start_btn.setEnabled(True)
        
        if success:
            self.status_label.setText(f"✓ 完成！文件已保存")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #28a745;
                    padding: 10px;
                    background-color: #d4edda;
                    border-radius: 5px;
                }
            """)
            QMessageBox.information(self, "成功", f"字幕添加完成！\n\n{message}")
        else:
            self.status_label.setText(f"✗ 失败")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #dc3545;
                    padding: 10px;
                    background-color: #f8d7da;
                    border-radius: 5px;
                }
            """)
            QMessageBox.critical(self, "错误", f"处理失败:\n{message}")
    
    def open_output_folder(self):
        """打开输出文件夹"""
        video_path = self.video_input.text()
        if video_path:
            folder = os.path.dirname(video_path)
            os.startfile(folder)
        else:
            QMessageBox.warning(self, "警告", "请先选择视频文件")
    
    def update_language(self):
        """更新语言（预留）"""
        pass
