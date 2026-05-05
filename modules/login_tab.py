"""
登录管理模块
"""
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QGroupBox, QPlainTextEdit, QDialog, QDialogButtonBox, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from playwright.sync_api import sync_playwright
from modules.i18n_manager import I18nManager

class LoginTab(QWidget):
    def __init__(self, data_dir):
        super().__init__()
        self.data_dir = data_dir
        self.i18n = I18nManager()
        self.cookie_file = os.path.join(data_dir, 'x_cookie.txt')
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        self.title = QLabel(self.i18n.t("x_login_title"))
        self.title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        layout.addWidget(self.title)
        
        # 按钮组（横向排列）
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.login_btn = QPushButton(self.i18n.t("btn_open_x"))
        self.login_btn.setMinimumHeight(50)
        self.login_btn.setFont(QFont("Microsoft YaHei", 10))
        self.login_btn.clicked.connect(self.open_login)
        btn_layout.addWidget(self.login_btn)
        
        self.save_btn = QPushButton(self.i18n.t("btn_save_cookie"))
        self.save_btn.setMinimumHeight(50)
        self.save_btn.setFont(QFont("Microsoft YaHei", 10))
        self.save_btn.clicked.connect(self.save_cookie)
        btn_layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton(self.i18n.t("btn_load_cookie"))
        self.load_btn.setMinimumHeight(50)
        self.load_btn.setFont(QFont("Microsoft YaHei", 10))
        self.load_btn.clicked.connect(self.load_cookie)
        btn_layout.addWidget(self.load_btn)
        
        self.import_btn = QPushButton(self.i18n.t("login_manual_import_btn"))
        self.import_btn.setMinimumHeight(50)
        self.import_btn.setFont(QFont("Microsoft YaHei", 10))
        self.import_btn.clicked.connect(self.import_cookie_manual)
        btn_layout.addWidget(self.import_btn)
        
        self.file_import_btn = QPushButton(self.i18n.t("login_file_import_btn"))
        self.file_import_btn.setMinimumHeight(50)
        self.file_import_btn.setFont(QFont("Microsoft YaHei", 10))
        self.file_import_btn.clicked.connect(self.import_cookie_from_file)
        btn_layout.addWidget(self.file_import_btn)
        
        layout.addLayout(btn_layout)
        
        # 说明区域
        self.info_group = QGroupBox(self.i18n.t("usage_instructions"))
        self.info_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        info_layout = QVBoxLayout()
        
        self.info_text = QLabel(self.i18n.t("login_usage_text"))
        self.info_text.setWordWrap(True)
        self.info_text.setStyleSheet("line-height: 150%; color: #555;")
        info_layout.addWidget(self.info_text)
        
        self.info_group.setLayout(info_layout)
        layout.addWidget(self.info_group)
        
        # 状态显示
        self.status_label = QLabel(self.i18n.t("status_not_logged_in"))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Microsoft YaHei", 10))
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def update_language(self):
        """更新界面语言"""
        self.title.setText(self.i18n.t("x_login_title"))
        self.login_btn.setText(self.i18n.t("btn_open_x"))
        self.save_btn.setText(self.i18n.t("btn_save_cookie"))
        self.load_btn.setText(self.i18n.t("btn_load_cookie"))
        self.info_group.setTitle(self.i18n.t("usage_instructions"))
        self.info_text.setText(self.i18n.t("login_usage_text"))
        self.status_label.setText(self.i18n.t("status_not_logged_in"))

    def open_login(self):
        try:
            # 先清理旧的资源
            if hasattr(self, 'browser') and self.browser:
                self.browser.close()
            if hasattr(self, 'playwright') and self.playwright:
                self.playwright.stop()
            
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=False,
                channel='chrome',
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-dev-shm-usage',
                ]
            )
            # 添加反检测脚本
            context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            self.page = context.new_page()
            # 隐藏 webdriver 属性
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
            """)
            # 不等待页面加载，立即返回让用户操作
            self.page.goto("https://x.com/home", timeout=5000)
            self.status_label.setText(self.i18n.t("login_status_logging"))
        except Exception as e:
            # 超时是正常的，因为用户需要手动登录
            if 'Timeout' in str(e) or 'timeout' in str(e):
                self.status_label.setText(self.i18n.t("login_status_logging"))
            else:
                QMessageBox.critical(self, self.i18n.t("failed"), self.i18n.t("login_browser_error").format(e))

    def save_cookie(self):
        if not hasattr(self, 'page'):
            QMessageBox.warning(self, self.i18n.t("warning"), self.i18n.t("login_save_first"))
            return
        
        try:
            cookies = self.page.context.cookies()
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(cookies, f)
            self.status_label.setText(self.i18n.t("login_status_logging"))
            QMessageBox.information(self, self.i18n.t("completed"), self.i18n.t("login_save_success"))
        except Exception as e:
            QMessageBox.critical(self, self.i18n.t("failed"), self.i18n.t("login_save_failed").format(e))

    def load_cookie(self):
        if not os.path.exists(self.cookie_file):
            QMessageBox.warning(self, self.i18n.t("warning"), self.i18n.t("login_no_cookie_file"))
            return
        
        try:
            # 先清理旧的资源
            if hasattr(self, 'browser') and self.browser:
                self.browser.close()
            if hasattr(self, 'playwright') and self.playwright:
                self.playwright.stop()
            
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=False,
                channel='chrome',
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-dev-shm-usage',
                ]
            )
            # 添加反检测脚本
            context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            self.page = context.new_page()
            # 隐藏 webdriver 属性
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
            """)
            
            import json
            with open(self.cookie_file, 'r') as f:
                cookies = json.load(f)
            
            # 调试：打印第一个 Cookie 的结构
            if cookies:
                print("加载的 Cookie 示例:", json.dumps(cookies[0], ensure_ascii=False, indent=2))
            
            self.page.context.add_cookies(cookies)
            
            # 不等待页面加载，让用户看到结果
            self.page.goto("https://x.com/home", timeout=5000)
            self.status_label.setText(self.i18n.t("login_verify_status"))
        except Exception as e:
            # 超时或两步验证页面是正常的
            if 'Timeout' in str(e) or 'timeout' in str(e) or 'two_step' in str(e):
                self.status_label.setText(self.i18n.t("login_verify_browser"))
            else:
                QMessageBox.critical(self, self.i18n.t("failed"), self.i18n.t("login_browser_error").format(e))
    
    def import_cookie_manual(self):
        """手动导入 Cookie"""
        dialog = QDialog(self)
        dialog.setWindowTitle(self.i18n.t("login_dialog_title"))
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 说明文本
        info = QLabel(self.i18n.t("login_dialog_info"))
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # 输入框
        text_edit = QPlainTextEdit()
        text_edit.setPlaceholderText(self.i18n.t("login_dialog_placeholder"))
        layout.addWidget(text_edit)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                import json
                cookie_text = text_edit.toPlainText().strip()
                
                if not cookie_text:
                    QMessageBox.warning(self, self.i18n.t("warning"), self.i18n.t("login_cookie_empty"))
                    return
                
                # 自动检测格式并解析
                lines = cookie_text.split('\n')
                if lines and '\t' in lines[0]:
                    # TSV 格式（从 Chrome DevTools 复制）
                    cookies = self.parse_tsv_cookies(cookie_text)
                else:
                    # 普通文本或 JSON 格式
                    cookies = self.parse_cookie_text(cookie_text)
                
                # 保存到文件
                with open(self.cookie_file, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f)
                
                self.status_label.setText(self.i18n.t("login_status_logging"))
                QMessageBox.information(self, self.i18n.t("completed"), self.i18n.t("login_import_success").format(len(cookies)))
                
            except Exception as e:
                QMessageBox.critical(self, self.i18n.t("failed"), self.i18n.t("login_import_failed").format(str(e)))
    
    def import_cookie_from_file(self):
        """从文件导入 Cookie"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.i18n.t("login_select_file_title"),
            "",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                import json
                
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    cookie_text = f.read().strip()
                
                if not cookie_text:
                    QMessageBox.warning(self, self.i18n.t("warning"), self.i18n.t("login_file_empty"))
                    return
                
                # 自动检测格式并解析
                lines = cookie_text.split('\n')
                if lines and '\t' in lines[0]:
                    # TSV 格式（从 Chrome DevTools 复制）
                    cookies = self.parse_tsv_cookies(cookie_text)
                else:
                    # 普通文本或 JSON 格式
                    cookies = self.parse_cookie_text(cookie_text)
                
                # 保存到标准位置
                with open(self.cookie_file, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f)
                
                self.status_label.setText(self.i18n.t("login_status_logging"))
                QMessageBox.information(self, self.i18n.t("completed"), self.i18n.t("login_file_import_success").format(len(cookies)))
                
            except Exception as e:
                QMessageBox.critical(self, self.i18n.t("failed"), self.i18n.t("login_file_import_failed").format(str(e)))
    
    def parse_cookie_text(self, cookie_text):
        """解析 Cookie 文本，支持 JSON 和文本格式"""
        import json
        
        # 尝试 JSON 格式
        try:
            cookies = json.loads(cookie_text)
            if isinstance(cookies, list):
                return cookies
        except:
            pass
        
        # 解析文本格式：name1=value1; name2=value2; ...
        cookies = []
        cookie_parts = cookie_text.split(';')
        
        for part in cookie_parts:
            part = part.strip()
            if '=' in part:
                name, value = part.split('=', 1)
                name = name.strip()
                value = value.strip()
                
                if name and value:
                    cookies.append({
                        'name': name,
                        'value': value,
                        'domain': '.x.com',
                        'path': '/',
                        'secure': True,
                        'httpOnly': True
                    })
        
        if not cookies:
            raise ValueError("无法解析 Cookie 格式，请确保格式正确")
        
        return cookies
    
    def parse_tsv_cookies(self, cookie_text):
        """解析 TSV 格式的 Cookie（从 Chrome DevTools 复制）"""
        from datetime import datetime
        
        lines = cookie_text.strip().split('\n')
        # 过滤空行
        lines = [line.strip() for line in lines if line.strip()]
        
        if not lines:
            raise ValueError("Cookie 文本为空")
        
        # 检查是否为 TSV 格式
        if '\t' not in lines[0]:
            raise ValueError("不是 TSV 格式，请使用 parse_cookie_text 方法")
        
        cookies = []
        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 2:
                name = parts[0].strip()
                value = parts[1].strip()
                domain = parts[2].strip() if len(parts) > 2 else '.x.com'
                path = parts[3].strip() if len(parts) > 3 else '/'
                http_only = '✓' in parts[6] if len(parts) > 6 else False
                secure = '✓' in parts[7] if len(parts) > 7 else False
                
                # 解析 expires 字段（时间戳格式）
                expires = -1
                if len(parts) > 4 and parts[4].strip():
                    expires_str = parts[4].strip()
                    if expires_str.lower() != 'session':
                        try:
                            # 尝试解析 ISO 格式时间
                            if 'T' in expires_str:
                                dt = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                                expires = dt.timestamp()
                        except:
                            pass
                
                if name and value:
                    cookie_dict = {
                        'name': name,
                        'value': value,
                        'domain': domain,
                        'path': path,
                        'secure': secure,
                        'httpOnly': http_only
                    }
                    if expires > 0:
                        cookie_dict['expires'] = expires
                    
                    cookies.append(cookie_dict)
        
        if not cookies:
            raise ValueError("无法解析 TSV 格式 Cookie")
        
        return cookies
