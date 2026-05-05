"""
X (Twitter) 自动发帖核心逻辑
支持图文配对、视频发布、进度保存和断点续传
"""
import os
import json
import time
import random
from playwright.sync_api import sync_playwright

class XAutoPost:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.cookie_file = os.path.join(data_dir, 'x_cookie.txt')
        self.progress_file = os.path.join(data_dir, 'post-progress.json')
    
    def get_last_posted_index(self):
        """获取上次发布的最后一个帖子编号"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('last_posted_index', 0)
        except:
            pass
        return 0
    
    def save_progress(self, index):
        """保存发布进度"""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump({'last_posted_index': index}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存进度失败: {e}")
    
    def reset_progress(self):
        """重置发布进度"""
        try:
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)
            return True
        except:
            return False
    
    def start_posting_single(self, img_path, text_path, callback=None, log_callback=None):
        """发布单个帖子"""
        
        def log(msg):
            print(msg)
            if log_callback:
                log_callback(msg)
        
        try:
            log('🌐 正在启动浏览器...')
            import sys
            playwright = sync_playwright().start()
            
            if getattr(sys, 'frozen', False):
                browser = playwright.chromium.launch(
                    headless=False,
                    channel='chrome',
                    args=['--start-maximized']
                )
            else:
                browser = playwright.chromium.launch(
                    headless=False,
                    channel='chrome',
                    args=['--start-maximized']
                )
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            
            # 加载 Cookie
            if os.path.exists(self.cookie_file):
                try:
                    with open(self.cookie_file, 'r', encoding='utf-8') as f:
                        cookies = json.load(f)
                    context.add_cookies(cookies)
                    log('✅ Cookie 已加载')
                except Exception as e:
                    log(f'⚠️ Cookie 加载失败: {str(e)}')
            
            page = context.new_page()
            
            # 页面加载重试机制
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    log(f'🔄 正在连接 X (尝试 {attempt + 1}/{max_retries})...')
                    page.goto('https://x.com/home', wait_until='domcontentloaded', timeout=60000)
                    time.sleep(3)
                    break
                except Exception as e:
                    log(f'⚠️ 连接失败: {str(e)}')
                    if attempt == max_retries - 1:
                        raise Exception('无法连接到 X，请检查网络或 Chrome 浏览器是否正常')
                    time.sleep(2)
            
            # 检查登录状态
            log('🔍 检查登录状态...')
            try:
                page.wait_for_selector('[data-testid="AppTabBar_Home_Link"]', timeout=30000)
                log('✅ 已进入 X 首页')
            except:
                log('❌ 未检测到 X 首页，可能未登录或页面加载失败')
                browser.close()
                playwright.stop()
                raise Exception('请先在浏览器中登录 X 账号')
            
            # 读取文案
            with open(text_path, 'r', encoding='utf-8') as f:
                text_content = f.read().strip()
            
            log(f'📝 文案: {text_content[:50]}...')
            
            # 等待页面加载完成
            log('⏳ 等待页面加载...')
            time.sleep(30)  # 等待30秒确保页面完全加载
            
            # 第一步：点击 Post 按钮打开发帖框
            log(' 正在查找 Post 按钮...')
            try:
                # 使用1.txt中的选择器 - 侧边栏的Post按钮
                post_button = page.query_selector('[data-testid="SideNav_NewTweet_Button"]')
                if post_button:
                    post_button.click()
                    log('✅ 已点击 Post 按钮')
                    time.sleep(3)  # 等待发帖框弹出
                else:
                    log('⚠️ 未找到 Post 按钮')
            except Exception as e:
                log(f'⚠️ 点击 Post 按钮失败: {str(e)}')
            
            # 第二步：点击文本输入框
            log('🔍 正在查找发帖框...')
            try:
                # X平台的发帖框选择器
                post_selectors = [
                    '[data-testid="tweetTextarea_0"]',
                    'div[role="textbox"][data-testid*="tweetTextarea"]',
                    'div.public-DraftEditor-content'
                ]
                post_box = None
                for selector in post_selectors:
                    try:
                        post_box = page.query_selector(selector)
                        if post_box:
                            log(f'✅ 找到发帖框: {selector}')
                            break
                    except:
                        continue
                
                if post_box:
                    post_box.click()
                    time.sleep(2)
                    log('✅ 已点击发帖框')
                else:
                    log('⚠️ 未找到发帖框，尝试直接聚焦')
                    # 尝试直接点击页面主体来激活发帖框
                    page.click('[data-testid="primaryColumn"]', timeout=5000)
                    time.sleep(2)
            except Exception as e:
                log(f'⚠️ 点击发帖框失败: {str(e)}')
            
            # 输入文案
            try:
                log('🔍 正在查找文本输入框...')
                textarea = page.query_selector('[data-testid="tweetTextarea_0"]')
                if textarea:
                    if text_content:
                        textarea.click()
                        time.sleep(1)
                        textarea.fill(text_content)
                        log('📝 文案已输入')
                        time.sleep(2)  # 等待按钮启用
                    else:
                        log('⚠️ 文案内容为空')
                else:
                    log('️ 未找到文本输入框')
            except Exception as e:
                log(f'️ 文案输入失败: {str(e)}')
            
            # 上传图片/视频
            if os.path.exists(img_path):
                log(f'📷 准备上传媒体: {os.path.basename(img_path)}')
                try:
                    # X平台使用隐藏的file input
                    page.evaluate('''
                        () => {
                            const inputs = document.querySelectorAll('input[type="file"]');
                            inputs.forEach(input => {
                                input.style.display = 'block';
                                input.style.opacity = '1';
                            });
                        }
                    ''')
                    time.sleep(1)
                    
                    file_input = page.query_selector('input[data-testid="fileInput"]')
                    if file_input:
                        file_input.set_input_files(img_path)
                        log(' 媒体已上传，等待处理...')
                        time.sleep(5)  # 等待媒体上传完成
                    else:
                        log('⚠️ 未找到文件输入元素')
                except Exception as e:
                    log(f'⚠️ 媒体上传失败: {str(e)}')
            
            # 点击发布按钮
            log(' 正在查找发布按钮...')
            time.sleep(3)  # 等待按钮启用
                        
            share_clicked = False
                        
            # 方式1: 使用6.txt中的选择器 - data-testid="tweetButton"
            try:
                post_btn = page.query_selector('[data-testid="tweetButton"]')
                if post_btn:
                    # 等待按钮启用（不是disabled状态）
                    log('⏳ 等待发布按钮启用...')
                    try:
                        page.wait_for_selector('[data-testid="tweetButton"]:not([aria-disabled="true"])', timeout=15000)
                        post_btn.click()
                        log('🚀 已点击发布按钮')
                        share_clicked = True
                    except:
                        log('⚠️ 发布按钮仍被禁用')
            except Exception as e:
                log(f'️ 发布按钮方式1失败: {str(e)}')
            
            # 方式2: JS模拟点击
            if not share_clicked:
                try:
                    result = page.evaluate('''
                        () => {
                            const buttons = Array.from(document.querySelectorAll('button'));
                            const target = buttons.find(el => el.innerText.includes('Post'));
                            if (target) {
                                target.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                return true;
                            }
                            return false;
                        }
                    ''')
                    if result:
                        log('🚀 已点击发布按钮 (JS)')
                        share_clicked = True
                except Exception as e:
                    log(f'⚠️ 发布按钮方式2失败: {str(e)}')
            
            if share_clicked:
                log('⏳ 等待发布完成...')
                time.sleep(10)  # 增加等待时间，确保帖子发布成功
                            
                log('✅ 帖子发布成功')
                            
                if callback:
                    callback(1, 1, "✅ 发布成功")
            else:
                log('❌ 未找到发布按钮，发帖失败')
                        
            # 发布后再等待一下确保完成
            log('⏳ 等待页面恢复...')
            time.sleep(5)
                        
            browser.close()
            playwright.stop()
            
            return 1
            
        except Exception as e:
            raise
    
    def start_posting(self, images_dir, texts_dir, callback=None, log_callback=None, single_post=False, start_index=None):
        """开始自动发帖
        single_post: True=只发1帖, False=批量发帖
        """
        
        def log(msg):
            print(msg)
            if log_callback:
                log_callback(msg)
        
        try:
            # 扫描图片和文案文件
            log('🔍 正在扫描文件...')
            image_files = sorted([f for f in os.listdir(images_dir) 
                                  if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.webp'))])
            text_files = sorted([f for f in os.listdir(texts_dir) 
                                 if f.lower().endswith('.txt')])
            
            if not image_files:
                raise Exception("图片文件夹为空")
            if not text_files:
                raise Exception("文案文件夹为空")
            
            # 构建 ID 配对
            pairs = []
            for img_file in image_files:
                base_name = os.path.splitext(img_file)[0]
                try:
                    img_id = int(base_name)
                    text_file = f"{img_id}.txt"
                    if text_file in text_files:
                        pairs.append({
                            'image': os.path.join(images_dir, img_file),
                            'text': os.path.join(texts_dir, text_file),
                            'id': img_id
                        })
                except ValueError:
                    continue
            
            if not pairs:
                raise Exception("未找到匹配的图文对（文件名需为数字，如 1.png 对应 1.txt）")
            
            # 按 ID 排序
            pairs.sort(key=lambda x: x['id'])
            
            # 确定起始索引
            last_index = self.get_last_posted_index()
            if start_index is not None:
                current_index = start_index
            else:
                current_index = last_index + 1
            
            # 过滤出待发布的帖子
            pending_pairs = [p for p in pairs if p['id'] >= current_index]
            
            if not pending_pairs:
                raise Exception(f"所有素材已发布完毕 (最后发布 ID: {last_index})。请更新文件夹或重置进度。")
            
            if single_post:
                log(f'✅ 找到 {len(pairs)} 组图文对，上次发布到 ID: {last_index}，本次将发布 ID: {pending_pairs[0]["id"]}')
                pending_pairs = [pending_pairs[0]]
            else:
                log(f'✅ 找到 {len(pairs)} 组图文对，上次发布到 ID: {last_index}，将从 ID: {current_index} 开始发布')
            
            # 启动浏览器
            log('🌐 正在启动浏览器...')
            import sys
            playwright = sync_playwright().start()
            
            if getattr(sys, 'frozen', False):
                browser = playwright.chromium.launch(
                    headless=False,
                    channel='chrome',
                    args=['--start-maximized']
                )
            else:
                browser = playwright.chromium.launch(
                    headless=False,
                    channel='chrome',
                    args=['--start-maximized']
                )
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            
            # 加载 Cookie
            if os.path.exists(self.cookie_file):
                try:
                    with open(self.cookie_file, 'r', encoding='utf-8') as f:
                        cookies = json.load(f)
                    context.add_cookies(cookies)
                    log('✅ Cookie 已加载')
                except Exception as e:
                    log(f'⚠️ Cookie 加载失败: {str(e)}')
            
            page = context.new_page()
            
            # 页面加载重试机制
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    log(f'🔄 正在连接 X (尝试 {attempt + 1}/{max_retries})...')
                    page.goto('https://x.com/home', wait_until='domcontentloaded', timeout=60000)
                    time.sleep(3)
                    break
                except Exception as e:
                    log(f'⚠️ 连接失败: {str(e)}')
                    if attempt == max_retries - 1:
                        raise Exception('无法连接到 X，请检查网络或 Chrome 浏览器是否正常')
                    time.sleep(2)
            
            # 检查登录状态
            log('🔍 检查登录状态...')
            try:
                # X平台的导航栏选择器
                page.wait_for_selector('[data-testid="AppTabBar_Home_Link"]', timeout=30000)
                log('✅ 已进入 X 首页')
            except:
                log('❌ 未检测到 X 首页，可能未登录或页面加载失败')
                browser.close()
                playwright.stop()
                raise Exception('请先在浏览器中登录 X 账号')
            
            post_count = 0
            
            # 循环发帖
            for pair in pending_pairs:
                try:
                    post_count += 1
                    if callback:
                        callback(post_count, len(pending_pairs), f"正在发布第 {post_count} 条帖子 (ID:{pair['id']})")
                    
                    log(f'📸 准备发布帖子 ID: {pair["id"]}')
                    
                    # 读取文案
                    with open(pair['text'], 'r', encoding='utf-8') as f:
                        text_content = f.read().strip()
                    
                    log(f'📝 文案: {text_content[:30]}...')
                    
                    # 点击发帖框
                    log(' 正在查找发帖框...')
                    try:
                        post_box = page.query_selector('text="你在想什么？"') or page.query_selector('text="What\'s on your mind?"')
                        if post_box:
                            post_box.click()
                            time.sleep(2)
                            log('✅ 已点击发帖框')
                        else:
                            # 尝试直接访问发帖页面
                            page.goto('https://x.com/', wait_until='domcontentloaded', timeout=30000)
                            time.sleep(3)
                            # 尝试查找发帖框
                            post_selectors = [
                                'text="What is happening?!"',
                                '[data-testid="tweetTextarea_0"]',
                                'div[role="textbox"]'
                            ]
                            for selector in post_selectors:
                                post_box = page.query_selector(selector)
                                if post_box:
                                    break
                            if post_box:
                                post_box.click()
                                time.sleep(2)
                    except Exception as e:
                        log(f'⚠️ 点击发帖框失败: {str(e)}')
                    
                    # 输入文案
                    try:
                        textarea = page.query_selector('div[contenteditable="true"][role="textbox"]')
                        if textarea:
                            if text_content:
                                textarea.fill(text_content)
                                log('📝 文案已输入')
                                time.sleep(1)
                    except Exception as e:
                        log(f'⚠️ 文案输入失败: {str(e)}')
                    
                    # 上传图片
                    if os.path.exists(pair['image']):
                        log(f'📷 准备上传图片: {pair["image"]}')
                        try:
                            # 显示隐藏的文件输入元素
                            page.evaluate("""
                                () => {
                                    const fileInput = document.querySelector('input[type="file"][accept*="image"]');
                                    if (fileInput) {
                                        fileInput.style.display = 'block';
                                        fileInput.style.visibility = 'visible';
                                        fileInput.style.opacity = '1';
                                    }
                                }
                            """)
                            time.sleep(1)
                            
                            file_input = page.query_selector('input[type="file"][accept*="image"]')
                            if file_input:
                                file_input.set_input_files(pair['image'])
                                log('📷 图片已上传')
                                time.sleep(5)
                            else:
                                log('⚠️ 未找到文件输入元素')
                        except Exception as e:
                            log(f'⚠️ 图片上传失败: {str(e)}')
                    
                    # 点击发布按钮
                    log('🔍 正在查找发布按钮...')
                    time.sleep(2)
                    
                    share_clicked = False
                    
                    # 方式1: 查找文本为"发布"的按钮
                    try:
                        post_btn = page.locator('button:has-text("发布"), button:has-text("Post")').first
                        if post_btn.count() > 0:
                            post_btn.click()
                            log('🚀 已点击发布按钮')
                            share_clicked = True
                    except Exception as e:
                        log(f'⚠️ 发布按钮方式1失败: {str(e)}')
                    
                    # 方式2: JS模拟点击
                    if not share_clicked:
                        try:
                            result = page.evaluate('''
                                () => {
                                    const buttons = Array.from(document.querySelectorAll('button, [role="button"]'));
                                    const target = buttons.find(el => el.innerText.includes('发布') || el.innerText.includes('Post'));
                                    if (target) {
                                        target.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                        return true;
                                    }
                                    return false;
                                }
                            ''')
                            if result:
                                log('🚀 已点击发布按钮 (JS)')
                                share_clicked = True
                        except Exception as e:
                            log(f'⚠️ 发布按钮方式2失败: {str(e)}')
                    
                    if share_clicked:
                        log(' 等待发布完成...')
                        time.sleep(random.uniform(5, 10))
                        
                        log(f'✅ 帖子 ID:{pair["id"]} 发布成功')
                        self.save_progress(pair['id'])
                        
                        if callback:
                            callback(post_count, len(pending_pairs), f"✅ 发布成功 (ID:{pair['id']})")
                    else:
                        log('❌ 未找到发布按钮，发帖失败')
                    
                    # 返回首页准备下一次发帖
                    try:
                        page.goto('https://x.com/home', wait_until='domcontentloaded', timeout=30000)
                        time.sleep(2)
                        log(' 已返回首页')
                    except:
                        pass
                    
                    # 随机延迟
                    time.sleep(random.uniform(30, 60))
                    
                except Exception as e:
                    log(f'❌ 处理帖子失败: {str(e)}')
                    continue
            
            browser.close()
            playwright.stop()
            
            return post_count
            
        except Exception as e:
            raise
