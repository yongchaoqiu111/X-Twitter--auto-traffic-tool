"""
X (Twitter) 自动引流工具 - 主程序入口
技术栈: PyQt6 + Playwright
"""
import sys
import os

# 打包后添加modules到路径
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

modules_path = os.path.join(application_path, 'modules')
if os.path.exists(modules_path) and modules_path not in sys.path:
    sys.path.insert(0, application_path)

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from modules.i18n_manager import I18nManager
from modules.login_tab import LoginTab
from modules.auto_post_tab import AutoPostTab
from modules.auto_join_community_tab import AutoJoinCommunityTab
from modules.video_download_tab import VideoDownloadTab


class XTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.i18n = I18nManager()
        self.setWindowTitle("X 自动引流工具 v1.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置数据目录
        if getattr(sys, 'frozen', False):
            self.data_dir = os.path.join(os.path.dirname(sys.executable), 'data')
        else:
            self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部作者信息栏和语言切换
        top_layout = QVBoxLayout()
        top_layout.setSpacing(5)
        
        # 作者信息
        self.author_bar = QLabel(self.i18n.t("author_bar"))
        self.author_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.author_bar.setFont(QFont("Microsoft YaHei", 10))
        self.author_bar.setStyleSheet("""
            QLabel {
                background-color: #000000;
                color: white;
                padding: 8px;
                border-radius: 5px;
            }
        """)
        top_layout.addWidget(self.author_bar)
        
        # 语言切换按钮
        lang_layout = QHBoxLayout()
        lang_layout.setSpacing(10)
        
        current_lang = self.i18n.get_current_language()
        btn_text = "EN" if current_lang == "zh" else "中文"
        self.lang_switch = QPushButton(btn_text)
        self.lang_switch.setFixedSize(80, 35)
        self.lang_switch.setStyleSheet("""
            QPushButton {
                background-color: #1DA1F2;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0d8bd9;
            }
        """)
        self.lang_switch.clicked.connect(self.on_lang_switch_clicked)
        lang_layout.addWidget(self.lang_switch)
        
        lang_layout.addStretch()
        top_layout.addLayout(lang_layout)
        
        main_layout.addLayout(top_layout)
        
        # 创建Tab控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("Microsoft YaHei", 10))
        
        # 添加各个功能Tab
        self.login_tab = LoginTab(self.data_dir)
        self.auto_post_tab = AutoPostTab(self.data_dir)
        self.join_community_tab = AutoJoinCommunityTab(self.data_dir)
        self.video_download_tab = VideoDownloadTab(self.data_dir)
        
        self.tab_widget.addTab(self.login_tab, self.i18n.t("tab_login"))
        self.tab_widget.addTab(self.auto_post_tab, self.i18n.t("x_post_title"))
        self.tab_widget.addTab(self.join_community_tab, self.i18n.t("x_join_community_title"))
        self.tab_widget.addTab(self.video_download_tab, self.i18n.t("video_download_title"))
        
        main_layout.addWidget(self.tab_widget)
    
    def on_lang_switch_clicked(self):
        """语言按钮点击"""
        current_lang = self.i18n.get_current_language()
        new_lang = "en" if current_lang == "zh" else "zh"
        self.i18n.set_language(new_lang)
        self.lang_switch.setText("中文" if new_lang == "en" else "EN")
        # 更新所有Tab的语言
        self.update_all_tabs_language()
        # 更新主窗口标题和Tab标签
        self.setWindowTitle(f"X {self.i18n.t('app_title')} v1.0")
        self.author_bar.setText(self.i18n.t("author_bar"))
        # 更新Tab标签
        self.tab_widget.setTabText(0, self.i18n.t("tab_login"))
        self.tab_widget.setTabText(1, self.i18n.t("x_post_title"))
        self.tab_widget.setTabText(2, self.i18n.t("x_join_community_title"))
        self.tab_widget.setTabText(3, self.i18n.t("video_download_title"))
    
    def update_all_tabs_language(self):
        """更新所有Tab的语言"""
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if hasattr(tab, 'update_language'):
                tab.update_language()

    def closeEvent(self, event):
        """窗口关闭时清理资源"""
        try:
            # 清理逻辑
            pass
        except:
            pass
        event.accept()


def main():
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        window = XTool()
        window.show()
        
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        print(f"程序启动失败: {e}")
        traceback.print_exc()
        input("按回车键退出...")


if __name__ == '__main__':
    main()
