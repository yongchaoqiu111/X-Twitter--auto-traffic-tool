# X Auto Traffic Tool (X 自动引流工具)

一款基于 PyQt6 和 Playwright 的 X (Twitter) 自动化桌面工具，支持批量发帖、自动加入社区、视频下载等功能，并提供完整的中英文国际化支持。

## ✨ 功能特性

- **登录管理** - Cookie 保存与加载，支持手动导入和文件导入
- **批量自动发帖** - 支持图片和视频发布，文件 ID 配对机制
- **自动加入社区** - 关键词搜索，自动发现并加入相关社区
- **视频下载** - 支持 X 平台视频下载
- **多语言支持** - 完整的中英文界面切换

## 🛠 技术栈

### 核心框架
- **Python 3.8+** - 主要开发语言
- **PyQt6 6.6.1** - 桌面 GUI 框架
- **Playwright 1.40.0** - 浏览器自动化库

### 依赖库
- **beautifulsoup4 4.12.2** - HTML 解析
- **requests 2.31.0** - HTTP 请求库
- **schedule 1.2.0** - 任务调度

### 架构设计
- **模块化架构** - 功能模块独立，易于扩展
- **多线程处理** - QThread 异步执行，避免 UI 阻塞
- **单例模式** - I18nManager 全局语言管理
- **信号槽机制** - PyQt6 信号系统，线程间通信

### 自动化技术
- **浏览器自动化** - Playwright 控制 Chromium 浏览器
- **Cookie 管理** - 持久化登录状态
- **反检测机制** - 隐藏 WebDriver 特征
- **智能等待** - 动态等待页面加载完成

## 📦 安装

### 环境要求
- Python 3.8 或更高版本
- Windows 10/11 (推荐)

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd X
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **安装 Playwright 浏览器**
```bash
playwright install
playwright install-deps
```

4. **运行程序**
```bash
python main.py
```

##  项目结构

```
X/
── main.py                      # 主程序入口
├── requirements.txt             # Python 依赖
├── modules/                     # 功能模块
│   ├── login_tab.py            # 登录管理界面
│   ├── auto_post_tab.py        # 自动发帖界面
│   ├── auto_post.py            # 发帖核心逻辑
│   ├── auto_post_worker.py     # 发帖工作线程
│   ├── auto_join_community_tab.py  # 加入社区界面
│   ├── auto_join_community.py  # 加入社区核心逻辑
│   ├── auto_join_community_worker.py  # 加入社区工作线程
│   ├── video_download_tab.py   # 视频下载界面
│   ├── i18n_manager.py         # 国际化管理器
│   ├── automation_engine.py    # 自动化引擎
│   └── utils.py                # 工具函数
├── i18n/                        # 国际化文件
│   ├── zh.json                 # 中文翻译
│   └── en.json                 # 英文翻译
├── data/                        # 数据目录
│   ├── x_cookie.txt            # Cookie 存储
│   └── downloads/              # 下载文件
└── 1/ & 2/                     # 媒体和文案文件夹
```

## 🚀 使用指南

### 1. 登录管理
- 点击"打开浏览器登录 X"
- 在弹出的浏览器中手动完成登录
- 点击"保存当前 Cookie"保存登录状态
- 点击"加载 Cookie 测试"验证 Cookie 有效性

### 2. 批量发帖
- 准备媒体文件 (图片/视频) 到 `D:\weibo\X\1` 目录
- 准备文案文件 (TXT) 到 `D:\weibo\X\2` 目录
- 文件命名规则：`1.jpg`, `2.mp4`, `1.txt`, `2.txt` 等
- 在下拉菜单中选择对应的媒体和文案文件
- 点击"开始批量自动发帖"

### 3. 自动加入社区
- 在关键词管理表格中添加搜索关键词
- 设置最大加入数量
- 点击"开始搜索并加入"
- 系统会随机选择关键词，搜索并自动加入社区

### 4. 视频下载
- 复制 X 视频分享链接
- 粘贴到输入框
- 点击"下载视频"
- 视频将自动保存到 `data/downloads` 目录

## 🌐 国际化

支持中英文实时切换：
- 点击顶部语言切换按钮
- 所有界面文本立即更新
- 翻译文件位于 `i18n/` 目录
- 易于扩展其他语言

## ️ 注意事项

1. **合法使用** - 请遵守 X 平台的使用条款和机器人政策
2. **频率控制** - 内置随机延迟，避免触发反垃圾机制
3. **Cookie 安全** - Cookie 文件存储在本地，请妥善保管
4. **网络环境** - 需要稳定的网络连接访问 X 平台

## 📝 开发说明

### 添加新功能
1. 在 `modules/` 目录创建新模块
2. 继承 `QWidget` 创建 UI 界面
3. 实现 `update_language()` 方法支持国际化
4. 在 `main.py` 中注册新的 Tab

### 添加翻译
1. 在 `i18n/zh.json` 和 `i18n/en.json` 中添加键值对
2. 使用 `self.i18n.t("key_name")` 获取翻译文本
3. 调用 `update_language()` 更新界面

### 线程安全
- 使用 `QThread` 执行长时间任务
- 通过 `pyqtSignal` 传递进度和结果
- 主线程保持 UI 响应

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献指南
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 **Apache License 2.0** 开源许可证 - 详见 [LICENSE](LICENSE) 文件

## 👤 作者

**Chase Qiu (永超·邱)**

### 专业背景
专注企业级AI系统架构设计、大模型落地、RAG/Agent工程化开发实战干货。

### 合作方向
- **架构咨询**：AI系统架构设计与技术选型
- **项目搭案**：从0到1的AI项目搭建与实施  
- **技术方案输出**：定制化技术解决方案

### 联系方式
- **QQ**: 86609013
- **主页**: [ChaseQiu.top](https://chaseqiu.top)
- **私信说明需求，可获取初步思路**

##  致谢

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - 优秀的 Python GUI 框架
- [Playwright](https://playwright.dev/) - 强大的浏览器自动化库
- 所有贡献者和使用者

## 📮 联系方式

如有问题或建议，欢迎通过以下方式联系：
- GitHub Issues
- QQ: 86609013
- 网站: chaseqiu.top

---

**Disclaimer**: This tool is for educational and research purposes only. Users are responsible for complying with X's Terms of Service and applicable laws.

**免责声明**: 本工具仅用于教育和研究目的。使用者需自行遵守 X 平台服务条款和适用法律法规。
