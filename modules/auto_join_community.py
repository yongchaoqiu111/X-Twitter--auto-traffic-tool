"""
自动加入小组核心逻辑
"""
import os
import json
import time
import random
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

class XAutoJoinCommunity:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.cookie_file = os.path.join(data_dir, 'x_cookie.txt')
    
    def start_join_groups(self, group_keywords, callback=None, log_callback=None):
        """开始自动加入小组"""
        
        def log(msg):
            print(msg)
            if log_callback:
                log_callback(msg)
        
        try:
            log('🌐 正在启动浏览器...')
            playwright = sync_playwright().start()
            browser = playwright.chromium.launch(
                headless=False,
                channel='chrome',
                args=['--start-maximized']
            )
            context = browser.new_context()
            
            # 加载 Cookie
            if os.path.exists(self.cookie_file):
                with open(self.cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                context.add_cookies(cookies)
                log('✅ Cookie 已加载')
            
            page = context.new_page()
            
            # 第一步：进入首页验证登录状态
            log('🔍 正在验证登录状态...')
            page.goto('https://x.com/home', wait_until='domcontentloaded', timeout=30000)
            time.sleep(5)
            
            # 验证登录
            try:
                page.wait_for_selector('[data-testid="AppTabBar_Home_Link"]', timeout=10000)
                log('✅ 登录验证成功')
            except PlaywrightTimeout:
                raise Exception("Cookie 可能已过期，请重新保存")
            
            joined_count = 0
            total_keywords = len(group_keywords)
            
            # 随机选择一个关键词
            selected_keyword = random.choice(group_keywords)
            log(f'🎲 随机选择关键词: {selected_keyword}')
            
            if callback:
                callback(1, 1, f"正在搜索: {selected_keyword}")
            
            log(f'🔍 正在搜索社区: {selected_keyword}')
            
            # 直接使用URL参数搜索并跳转
            search_url = f"https://x.com/i/communities/suggested?q={selected_keyword}"
            log(f'🔄 正在跳转到: {search_url}')
            page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(15)  # 等待页面完全加载
            
            # 滚动页面以触发懒加载
            log('📜 滚动页面加载更多内容...')
            for i in range(3):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                time.sleep(3)
                    
            # 查找社区列表（X 社区链接通常是 /i/communities/xxx）
            log('🔍 正在查找社区链接...')
            all_links = page.query_selector_all('a[href^="/i/communities/"]')
            
            # 使用正则过滤，只保留纯数字ID的社区链接
            communities = []
            pattern = re.compile(r'^/i/communities/\d+$')
            for link in all_links:
                href = link.get_attribute('href')
                if href and pattern.match(href):
                    communities.append(link)
            
            log(f'📊 找到 {len(communities)} 个社区链接')
            
            if not communities:
                log(f'⚠️ 未找到匹配的社区: {selected_keyword}')
                # 尝试等待更长时间
                time.sleep(10)
                all_links = page.query_selector_all('a[href^="/i/communities/"]')
                communities = []
                pattern = re.compile(r'^/i/communities/\d+$')
                for link in all_links:
                    href = link.get_attribute('href')
                    if href and pattern.match(href):
                        communities.append(link)
                log(f'📊 再次查找，找到 {len(communities)} 个社区链接')
                
                if not communities:
                    browser.close()
                    playwright.stop()
                    return 0
            
            # 提取第一个社区链接并拼接完整URL
            first_community = communities[0]
            href = first_community.get_attribute('href')
            community_url = f"https://x.com{href}"
            log(f'📌 找到社区: {community_url}')
            
            # 跳转到社区页面
            log('🔄 正在进入社区页面...')
            page.goto(community_url, wait_until='domcontentloaded', timeout=15000)
            time.sleep(10)  # 等待页面完全加载
            
            # 尝试查找加入按钮
            join_selectors = [
                'button[aria-label*="Ask to join"]',
                'button[aria-label*="Join"]',
                'text="Ask to join"',
                'text="Join"',
                'text="加入"'
            ]
            
            join_button = None
            for selector in join_selectors:
                try:
                    join_button = page.query_selector(selector)
                    if join_button:
                        log(f'✅ 找到加入按钮: {selector}')
                        break
                except:
                    continue
            
            if join_button:
                # 检查是否已加入
                button_text = join_button.inner_text().strip()
                if button_text in ['已加入', 'Joined', '成员', 'Member', '已在社区中']:
                    log(f'⏭️ 已加入该社区，跳过')
                    if callback:
                        callback(1, 1, f"已加入，跳过: {selected_keyword}")
                    joined_count += 1
                else:
                    # 点击加入
                    log('🖱️ 正在点击加入按钮...')
                    join_button.click()
                    time.sleep(5)  # 等待点击生效
                    
                    # 等待可能的确认弹窗
                    try:
                        confirm_btn = page.query_selector('text="确认"') or page.query_selector('text="Confirm"')
                        if confirm_btn:
                            log('✅ 找到确认按钮，点击确认')
                            confirm_btn.click()
                            time.sleep(3)
                    except:
                        pass
                    
                    log(f'✅ 已申请加入社区: {selected_keyword}')
                    if callback:
                        callback(1, 1, f"✅ 已加入: {selected_keyword}")
                    joined_count += 1
            else:
                log(f'⚠️ 未找到加入按钮，可能已加入或需要审批: {selected_keyword}')
                if callback:
                    callback(1, 1, f"需要审批或已加入: {selected_keyword}")
                joined_count += 1
            
            # 随机延迟
            log('⏳ 等待一段时间后继续...')
            time.sleep(random.uniform(8, 12))
            
            browser.close()
            playwright.stop()
            
            log(f'🎉 任务完成，共处理 {joined_count} 个关键词')
            return joined_count
            
        except Exception as e:
            raise
