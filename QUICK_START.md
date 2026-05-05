# 快速开始指南

##  环境准备

### 1. 安装 Python

下载并安装 Python 3.8 或更高版本：
- 官网: https://www.python.org/downloads/
- 安装时勾选 "Add Python to PATH"

### 2. 克隆项目

```bash
git clone <repository-url>
cd X
```

### 3. 安装依赖

```bash
# 安装 Python 依赖包
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install

# 安装浏览器依赖 (Windows)
playwright install-deps
```

### 4. 运行程序

```bash
python main.py
```

##  快速使用

### 第一步：登录管理

1. 打开软件，进入 "Login Management" 标签页
2. 点击 "Open Browser to Login X"
3. 在弹出的浏览器中手动登录 X 账号
4. 点击 "Save Current Cookie" 保存登录状态
5. 点击 "Load Cookie Test" 验证 Cookie 有效性

### 第二步：批量发帖

1. 准备文件：
   - 图片/视频放入 `D:\weibo\X\1` 目录
   - 文案 TXT 文件放入 `D:\weibo\X\2` 目录
   - 文件命名：`1.jpg`, `2.mp4`, `1.txt`, `2.txt` 等

2. 在软件中选择：
   - 进入 "X Batch Auto Post" 标签页
   - 点击 "刷新" 按钮刷新文件列表
   - 从下拉菜单选择媒体文件和文案文件

3. 开始发帖：
   - 点击 "Start Batch Auto Posting"
   - 等待自动化完成

### 第三步：自动加入社区

1. 进入 "X Auto Join Communities" 标签页
2. 添加关键词：
   - 在输入框输入关键词 (如: AI, Technology)
   - 点击 "Add" 按钮添加到列表
3. 设置最大加入数量 (默认: 5)
4. 点击 "Start Search and Join"
5. 系统会自动搜索并加入社区

### 第四步：视频下载

1. 进入 "X Video Download" 标签页
2. 复制 X 视频分享链接
3. 粘贴到输入框
4. 点击 "Download Video"
5. 视频将保存到 `data/downloads` 目录

## 💡 使用技巧

### 1. 文件配对规则

程序会自动根据文件名数字配对：
- `1.jpg` + `1.txt` = 第一条帖子
- `2.mp4` + `2.txt` = 第二条帖子
- 依此类推...

### 2. Cookie 管理

- Cookie 保存在 `data/x_cookie.txt`
- 如果登录失效，重新保存 Cookie
- 定期验证 Cookie 有效性

### 3. 安全使用

- 避免过于频繁的操作
- 内置随机延迟，无需担心
- 遵守 X 平台使用条款

### 4. 语言切换

- 点击顶部 "中文" / "EN" 按钮
- 界面立即切换语言
- 所有功能保持一致

## ⚠️ 常见问题

### Q1: 浏览器无法启动？

**A**: 确保已运行 `playwright install` 安装浏览器

### Q2: Cookie 保存失败？

**A**: 确保已在浏览器中完成登录，再点保存

### Q3: 发帖失败？

**A**: 
- 检查 Cookie 是否有效
- 确认文件路径正确
- 查看错误提示信息

### Q4: 找不到社区？

**A**:
- 确保关键词拼写正确
- 尝试使用英文关键词
- 检查网络连接

### Q5: 视频下载失败？

**A**:
- 确认视频链接完整
- 检查 Cookie 是否有效
- 查看是否有下载权限

## 📧 获取帮助

遇到问题？

1. 查看 README.md 文档
2. 查看 TECH_STACK.md 技术文档
3. 提交 GitHub Issue
4. 联系作者 QQ: 86609013

## 🎉 开始使用

现在你已经准备好了！运行程序，开始自动化之旅吧！

```bash
python main.py
```

祝使用愉快！
