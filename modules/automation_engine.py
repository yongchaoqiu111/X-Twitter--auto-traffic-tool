"""
Facebook 自动化执行引擎
负责执行搜索、监控、AI 交互和自动回复
"""
import time
import random
import json
import os
import requests
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class AutomationWorker(QObject):
    """自动化工作线程（唯一操作 Playwright 的线程）"""
    # 信号定义
    log_signal = pyqtSignal(str)  # 日志输出
    status_signal = pyqtSignal(str)  # 状态更新
    finished_signal = pyqtSignal(bool, str)  # 完成信号 (成功/失败, 消息)
    
    def __init__(self, data_dir, config):
        super().__init__()
        self.data_dir = data_dir
        self.config = config
        self.playwright = None
        self.browser = None
        self.page = None
        self.is_running = False
        self.processed_comments = set()  # 已处理评论 ID 集合（防重复）
        
    def log(self, message):
        """输出日志并发送到 UI"""
        print(f"[Engine] {message}")
        self.log_signal.emit(message)
    
    def load_cookie_and_login(self):
        """加载 Cookie 并登录 Facebook"""
        cookie_file = os.path.join(self.data_dir, 'facebook_cookie.txt')
        if not os.path.exists(cookie_file):
            return False, "未找到 Cookie 文件，请先在【登录管理】中保存 Cookie"
        
        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=False,
                channel='chrome',
                args=['--start-maximized']
            )
            
            context = self.browser.new_context()
            context.add_cookies(cookies)
            self.page = context.new_page()
            
            self.log("🔄 正在加载 Cookie 并登录 Facebook...")
            self.page.goto("https://www.facebook.com", wait_until='domcontentloaded', timeout=30000)
            time.sleep(3)
            
            # 验证是否登录成功（检查是否有主页元素）
            try:
                self.page.wait_for_selector('[data-pagelet="LeftRail"]', timeout=5000)
                self.log("✅ Cookie 加载成功，已登录 Facebook")
                return True, "登录成功"
            except PlaywrightTimeout:
                return False, "Cookie 可能已过期，请重新保存"
                
        except Exception as e:
            return False, f"登录失败: {str(e)}"
    
    def search_and_join_groups(self):
        """搜索并进入目标群组"""
        group_keywords = self.config.get("group_keywords", [])
        if not group_keywords:
            self.log("⚠️ 未配置群组关键词")
            return []
        
        entered_groups = []
        
        for keyword in group_keywords:
            if not self.is_running:
                break
                
            self.log(f"🔍 正在搜索群组: {keyword}")
            self.status_signal.emit(f"正在搜索: {keyword}")
            
            try:
                search_url = f"https://www.facebook.com/search/groups/?q={keyword}"
                self.page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
                time.sleep(random.uniform(3, 5))
                
                # 尝试点击第一个群组
                try:
                    group_link = self.page.query_selector('a[href*="/groups/"]')
                    if group_link:
                        href = group_link.get_attribute('href')
                        self.page.goto(f"https://www.facebook.com{href}", wait_until='domcontentloaded', timeout=15000)
                        time.sleep(random.uniform(2, 4))
                        entered_groups.append(href)
                        self.log(f"✅ 已进入群组: {keyword}")
                    else:
                        self.log(f"⚠️ 未找到匹配的群组: {keyword}")
                except Exception as e:
                    self.log(f"⚠️ 进入群组失败: {str(e)}")
                
                # 随机延迟
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                self.log(f"❌ 搜索群组失败: {str(e)}")
        
        return entered_groups
    
    def call_llm_api(self, comment_text):
        """调用 LLM API 生成回复"""
        sys_config_file = os.path.join(self.data_dir, 'config.json')
        if not os.path.exists(sys_config_file):
            return "【错误】未配置系统设置"
        
        with open(sys_config_file, 'r', encoding='utf-8') as f:
            sys_config = json.load(f)
        
        api_key = sys_config.get("llm_api_key")
        base_url = sys_config.get("llm_base_url", "https://api.openai.com/v1")
        model = sys_config.get("llm_model", "gpt-3.5-turbo")
        system_prompt = sys_config.get("system_prompt", "你是一个友好的社群助手。")
        
        if not api_key:
            return "【错误】未配置 API Key"
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请回复这条评论（简短友好，不超过50字）：{comment_text}"}
            ],
            "temperature": 0.8,
            "max_tokens": 100
        }
        
        try:
            resp = requests.post(f"{base_url}/chat/completions", json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            reply = resp.json()["choices"][0]["message"]["content"]
            return reply.strip()
        except Exception as e:
            return f"【API 错误】{str(e)}"
    
    def get_fixed_reply(self, keyword, comment_text):
        """从配置中获取固定回复"""
        trigger_rules = self.config.get("trigger_rules", [])
        
        for rule in trigger_rules:
            if rule['keyword'] == keyword and rule.get('type') == 'fixed':
                replies = rule.get('replies', '').split('|')
                if replies:
                    return random.choice([r.strip() for r in replies if r.strip()])
        return None
    
    def monitor_and_reply(self):
        """监控评论区并自动回复"""
        trigger_rules = self.config.get("trigger_rules", [])
        if not trigger_rules:
            self.log("⚠️ 未配置触发规则")
            return
        
        self.log("👀 开始监控评论区...")
        self.status_signal.emit("正在监控评论...")
        
        while self.is_running:
            try:
                # 获取所有评论
                comments = self.page.query_selector_all('div[role="comment"]')
                
                for comment in comments:
                    if not self.is_running:
                        break
                    
                    # 获取评论 ID 和内容
                    comment_id = comment.get_attribute('data-commentid') or comment.get_attribute('id')
                    if not comment_id or comment_id in self.processed_comments:
                        continue
                    
                    try:
                        comment_text_elem = comment.query_selector('span[dir="auto"]')
                        if not comment_text_elem:
                            continue
                        
                        comment_text = comment_text_elem.inner_text().strip()
                        if not comment_text:
                            continue
                        
                        # 检查是否命中触发词
                        matched_rule = None
                        for rule in trigger_rules:
                            if rule['keyword'] in comment_text:
                                matched_rule = rule
                                break
                        
                        if matched_rule:
                            self.log(f"⚡ 命中评论: {comment_text[:30]}...")
                            self.processed_comments.add(comment_id)
                            
                            # 获取回复内容
                            reply_text = ""
                            if matched_rule.get('type') == 'ai':
                                self.log("🤖 正在调用 AI 生成回复...")
                                self.status_signal.emit("AI 正在生成回复...")
                                reply_text = self.call_llm_api(comment_text)
                            else:
                                reply_text = self.get_fixed_reply(matched_rule['keyword'], comment_text)
                            
                            if reply_text and not reply_text.startswith("【错误"):
                                self.log(f"💬 准备回复: {reply_text}")
                                self.status_signal.emit(f"正在回复: {reply_text[:20]}...")
                                
                                # 点击回复按钮
                                try:
                                    reply_button = comment.query_selector('text="回复"')
                                    if not reply_button:
                                        reply_button = comment.query_selector('text="Reply"')
                                    
                                    if reply_button:
                                        reply_button.click()
                                        time.sleep(1)
                                        
                                        # 输入回复内容
                                        input_box = self.page.query_selector('div[contenteditable="true"][role="textbox"]')
                                        if input_box:
                                            input_box.fill(reply_text)
                                            time.sleep(0.5)
                                            
                                            # 点击发送
                                            send_btn = self.page.query_selector('div[aria-label*="发送"]') or self.page.query_selector('text="发送"')
                                            if send_btn:
                                                send_btn.click()
                                                self.log("✅ 回复成功")
                                                self.status_signal.emit("回复成功")
                                                time.sleep(random.uniform(2, 4))
                                            else:
                                                self.log("⚠️ 未找到发送按钮")
                                        else:
                                            self.log("⚠️ 未找到输入框")
                                    else:
                                        self.log("⚠️ 未找到回复按钮")
                                except Exception as e:
                                    self.log(f"⚠️ 回复操作失败: {str(e)}")
                            else:
                                self.log(f"⚠️ 回复内容为空或出错: {reply_text}")
                    
                    except Exception as e:
                        self.log(f"⚠️ 处理单条评论失败: {str(e)}")
                        continue
                
                # 等待一段时间后刷新
                time.sleep(random.uniform(8, 12))
                
            except Exception as e:
                self.log(f"❌ 监控循环出错: {str(e)}")
                time.sleep(5)
    
    def run(self):
        """主执行流程"""
        self.is_running = True
        self.log("🚀 自动化引擎启动...")
        self.status_signal.emit("正在初始化...")
        
        try:
            # 1. 登录
            success, msg = self.load_cookie_and_login()
            if not success:
                self.finished_signal.emit(False, msg)
                return
            
            # 2. 搜索并进入群组
            groups = self.search_and_join_groups()
            if not groups:
                self.finished_signal.emit(False, "未能进入任何群组")
                return
            
            self.status_signal.emit("已进入群组，开始监控...")
            
            # 3. 监控并回复
            self.monitor_and_reply()
            
            self.finished_signal.emit(True, "自动化任务完成")
            
        except Exception as e:
            self.log(f"❌ 执行出错: {str(e)}")
            self.finished_signal.emit(False, str(e))
        finally:
            self.cleanup()
    
    def stop(self):
        """停止执行"""
        self.is_running = False
        self.log("🛑 收到停止信号")
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except:
            pass
        self.log("🧹 资源已清理")


class AutomationManager:
    """自动化管理器（UI 调用接口）"""
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.worker = None
        self.thread = None
    
    def start(self, config, log_callback=None, status_callback=None):
        """启动自动化任务"""
        # 加载配置
        import json
        config_file = os.path.join(self.data_dir, 'workflow_config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        # 创建工作线程
        self.thread = QThread()
        self.worker = AutomationWorker(self.data_dir, config)
        self.worker.moveToThread(self.thread)
        
        # 连接信号
        if log_callback:
            self.worker.log_signal.connect(log_callback)
        if status_callback:
            self.worker.status_signal.connect(status_callback)
        
        self.worker.finished_signal.connect(self._on_finished)
        
        # 启动线程
        self.thread.started.connect(self.worker.run)
        self.thread.start()
        
        return True
    
    def stop(self):
        """停止任务"""
        if self.worker:
            self.worker.stop()
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
    
    def _on_finished(self, success, message):
        """任务完成回调"""
        print(f"[Manager] 任务完成: {success}, {message}")
