"""
自动加入社区 Tab 界面
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QGroupBox, QMessageBox, QTableWidget, QTableWidgetItem, 
                             QLineEdit, QHeaderView)
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QFont
from modules.utils import load_json, save_json
from modules.auto_join_community import XAutoJoinCommunity
from modules.auto_join_community_worker import AutoJoinCommunityWorker
from modules.i18n_manager import I18nManager
import os

class AutoJoinCommunityTab(QWidget):
    def __init__(self, data_dir):
        super().__init__()
        self.data_dir = data_dir
        self.i18n = I18nManager()
        self.config_file = os.path.join(data_dir, 'auto_join_config.json')
        self.auto_join = XAutoJoinCommunity(data_dir)
        self.worker = None
        
        # 确保数据文件存在
        if not os.path.exists(self.config_file):
            save_json(self.config_file, {"group_keywords": []})
        
        self.init_ui()
        self.refresh_table()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 标题
        self.title = QLabel(self.i18n.t("x_join_community_title"))
        self.title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        main_layout.addWidget(self.title)
        
        # 说明卡片
        self.info_group = QGroupBox(self.i18n.t("join_guide_group"))
        info_layout = QVBoxLayout()
        self.info_text = QLabel(self.i18n.t("join_guide_text"))
        self.info_text.setWordWrap(True)
        self.info_text.setStyleSheet("line-height: 150%; color: #555;")
        info_layout.addWidget(self.info_text)
        self.info_group.setLayout(info_layout)
        main_layout.addWidget(self.info_group)
        
        # 关键词管理区
        self.keyword_box = QGroupBox(self.i18n.t("keyword_title"))
        keyword_layout = QVBoxLayout()
        
        # 表格
        self.keyword_table = QTableWidget()
        self.keyword_table.setColumnCount(2)
        self.keyword_table.setHorizontalHeaderLabels([self.i18n.t("search_keyword_label"), self.i18n.t("btn_delete_selected")])
        self.keyword_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.keyword_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.keyword_table.setColumnWidth(1, 80)
        self.keyword_table.setMinimumHeight(200)
        keyword_layout.addWidget(self.keyword_table)
        
        # 添加行
        add_layout = QHBoxLayout()
        self.keyword_label = QLabel(self.i18n.t("search_keyword_label"))
        add_layout.addWidget(self.keyword_label)
        
        self.new_keyword_input = QLineEdit()
        self.new_keyword_input.setPlaceholderText(self.i18n.t("keyword_placeholder"))
        self.new_keyword_input.setMinimumHeight(40)
        add_layout.addWidget(self.new_keyword_input)
        
        self.add_btn = QPushButton(self.i18n.t("btn_add"))
        self.add_btn.setMinimumHeight(40)
        self.add_btn.clicked.connect(self.add_keyword)
        add_layout.addWidget(self.add_btn)
        keyword_layout.addLayout(add_layout)
        
        self.keyword_box.setLayout(keyword_layout)
        main_layout.addWidget(self.keyword_box)
        
        # 状态显示区
        self.control_group = QGroupBox(self.i18n.t("join_group_control"))
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
        
        # 数量设置
        count_layout = QHBoxLayout()
        self.max_groups_label = QLabel(self.i18n.t("max_groups_label"))
        count_layout.addWidget(self.max_groups_label)
        
        self.max_groups_input = QLineEdit("5")
        self.max_groups_input.setMaximumWidth(100)
        self.max_groups_input.setMinimumHeight(40)
        count_layout.addWidget(self.max_groups_input)
        count_layout.addStretch()
        main_layout.addLayout(count_layout)
        
        # 启动按钮
        self.start_btn = QPushButton(self.i18n.t("btn_start_join"))
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_btn.clicked.connect(self.start_join)
        main_layout.addWidget(self.start_btn)
        
        main_layout.addStretch()
        self.setLayout(main_layout)
    
    def refresh_table(self):
        """从 JSON 刷新表格显示"""
        config = load_json(self.config_file, {})
        
        self.keyword_table.setRowCount(0)
        for kw in config.get("group_keywords", []):
            row = self.keyword_table.rowCount()
            self.keyword_table.insertRow(row)
            self.keyword_table.setItem(row, 0, QTableWidgetItem(kw))
            
            del_btn = QPushButton(self.i18n.t("join_group_delete_btn"))
            del_btn.setStyleSheet("color: red;")
            del_btn.clicked.connect(lambda checked, k=kw: self.delete_keyword(k))
            self.keyword_table.setCellWidget(row, 1, del_btn)
    
    def add_keyword(self):
        kw = self.new_keyword_input.text().strip()
        if not kw:
            return
        
        config = load_json(self.config_file, {})
        if "group_keywords" not in config:
            config["group_keywords"] = []
        
        if kw not in config["group_keywords"]:
            config["group_keywords"].append(kw)
            save_json(self.config_file, config)
            self.new_keyword_input.clear()
            self.refresh_table()
        else:
            QMessageBox.warning(self, self.i18n.t("warning"), self.i18n.t("join_group_keyword_exists"))
    
    def delete_keyword(self, kw):
        config = load_json(self.config_file, {})
        if kw in config.get("group_keywords", []):
            config["group_keywords"].remove(kw)
            save_json(self.config_file, config)
            self.refresh_table()
    
    def start_join(self):
        config = load_json(self.config_file, {})
        keywords = config.get("group_keywords", [])
        
        if not keywords:
            QMessageBox.warning(self, self.i18n.t("warning"), self.i18n.t("join_group_no_keywords"))
            return
        
        reply = QMessageBox.question(
            self, self.i18n.t("confirm"), 
            self.i18n.t("join_group_confirm_start").format(len(keywords)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.start_btn.setEnabled(False)
        self.status_label.setText(self.i18n.t("join_group_init_status"))
        self.status_label.setStyleSheet("color: green;")
        
        # 创建工作线程
        self.thread = QThread()
        self.worker = AutoJoinCommunityWorker(self.auto_join, keywords)
        self.worker.moveToThread(self.thread)
        
        # 连接信号
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.log.connect(self.on_log)
        
        # 启动线程
        self.thread.started.connect(self.worker.start_join)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()
    
    def on_progress(self, current, total, message):
        self.progress_label.setText(self.i18n.t("progress_format").format(current, total))
        self.status_label.setText(self.i18n.t("current_status") + " " + message)
        self.show_message(message, "blue")
    
    def on_log(self, message):
        current_text = self.message_label.text()
        if current_text and current_text.startswith("[日志]"):
            self.message_label.setText(current_text + "\n" + message)
        else:
            self.message_label.setText("[日志]\n" + message)
    
    def on_finished(self, success, message, count):
        self.start_btn.setEnabled(True)
        if success:
            self.status_label.setText(self.i18n.t("status_completed_count").format(count))
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
        self.title.setText(self.i18n.t("x_join_community_title"))
        self.info_group.setTitle(self.i18n.t("join_guide_group"))
        self.info_text.setText(self.i18n.t("join_guide_text"))
        self.keyword_box.setTitle(self.i18n.t("keyword_title"))
        self.keyword_table.setHorizontalHeaderLabels([self.i18n.t("search_keyword_label"), self.i18n.t("btn_delete_selected")])
        self.keyword_label.setText(self.i18n.t("search_keyword_label"))
        self.new_keyword_input.setPlaceholderText(self.i18n.t("keyword_placeholder"))
        self.add_btn.setText(self.i18n.t("btn_add"))
        self.max_groups_label.setText(self.i18n.t("max_groups_label"))
        self.control_group.setTitle(self.i18n.t("join_group_control"))
        self.start_btn.setText(self.i18n.t("btn_start_join"))
        
        # 更新表格中的删除按钮
        for row in range(self.keyword_table.rowCount()):
            del_btn = self.keyword_table.cellWidget(row, 1)
            if del_btn:
                del_btn.setText(self.i18n.t("join_group_delete_btn"))
