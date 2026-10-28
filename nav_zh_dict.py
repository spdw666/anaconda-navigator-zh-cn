# -*- coding: utf-8 -*-
"""Anaconda Navigator 简体中文词条表。

键 = 源码里的英文原文（必须逐字节一致，含标点/首尾空格/HTML 标签）
值 = 简体中文译文

原则：
- 这里只收静态界面文案；公开课程/应用介绍在独立内容词典中，按控件字段翻译。
- 用户数据保护由 zhcn_boot / nav_content 的控件语义规则实现。
  整串匹配本身不识别数据类型，合法环境名也可能恰好与英文词条同名。
- 不做子串替换，只做整串精确匹配。
"""

ZH = {
    # ===== 主窗口 / 顶栏 / 菜单 =====
    'Anaconda Navigator': 'Anaconda 导航器',
    'Anaconda Navigator.': 'Anaconda 导航器。',
    'About Anaconda Navigator': '关于 Anaconda 导航器',
    'Anaconda Navigator Information': 'Anaconda 导航器信息',
    'Anaconda Navigator Startup Error': 'Anaconda 导航器启动错误',
    'Anaconda Navigator cannot be run with root user privileges.':
        'Anaconda 导航器不能以 root 用户权限运行。',
    'Home': '主页',
    'Environments': '环境',
    'Learning': '学习',
    'Community': '社区',
    '&File': '&文件',
    '&Help': '&帮助',
    '&Edit': '&编辑',
    '&View': '&视图',
    '&Preferences': '&首选项',
    '&Restart': '&重启',
    '&Quit': '&退出',
    '&Online Documentation': '&在线文档',
    '&Logs viewer': '&日志查看器',
    '&About': '&关于',
    '&Copy': '&复制',
    '&Paste': '&粘贴',
    "What's new": '新特性',
    'Update Now': '立即更新',

    # ===== 启动 / 加载提示 =====
    'Preparing interface...': '正在准备界面…',
    'Loading user...': '正在加载用户…',
    'Loading bundled metadata...': '正在加载内置元数据…',
    'Loading applications...': '正在加载应用…',
    'Loading environments...': '正在加载环境…',
    'Collecting sources...': '正在收集来源…',
    'Updating package index and metadata...': '正在更新包索引与元数据…',
    'Refreshing applications': '正在刷新应用',
    'Loading packages of <b>': '正在加载包：<b>',
    'Verifying <b>anaconda-toolbox</b> on <b>': '正在验证 <b>anaconda-toolbox</b> 于 <b>',
    '<i>Working in offline mode</i>': '<i>离线模式运行中</i>',
    'Connect to Navigator': '正在连接导航器',

    # ===== 首页 / 应用卡片 =====
    'All applications': '所有应用',
    'Installed applications': '已安装应用',
    'Not installed applications': '未安装应用',
    'Updatable applications': '可更新应用',
    'Channels': '频道',
    'Launch': '启动',
    'Install': '安装',
    'Install application': '安装应用',
    'Update application': '更新应用',
    'Remove application': '移除应用',
    'Update Application': '更新应用',
    'Application options': '应用选项',
    'Application icon is missing from the package recipe': '包配方中缺少应用图标',
    'Application icon will show when installed': '安装后将显示应用图标',
    'Install specific version': '安装指定版本',
    'Mark for specific version installation': '标记为安装指定版本',
    'Incomplete application description': '应用描述不完整',
    'Installer does not contain any applications': '安装程序不包含任何应用',
    'installer requires user to accept license agreement': '安装程序需要用户接受许可协议',
    'Access Anaconda Assistant in Jupyter Notebooks and JupyterLab.':
        '在 Jupyter Notebook 与 JupyterLab 中使用 Anaconda 助手。',
    'Documentation': '文档',
    'Homepage': '主页',
    'Issue Tracker': '问题追踪',
    'Anaconda Cloud': 'Anaconda 云端',
    'Development': '开发版',
    'All': '全部',

    # ===== 环境页 =====
    'Create': '创建',
    'Clone': '克隆',
    'Import': '导入',
    'Backup': '备份',
    'Remove': '移除',
    'Search': '搜索',
    'Search...': '搜索…',
    'Search Environments': '搜索环境',
    'Search Packages': '搜索包',
    'Open Terminal': '打开终端',
    'Open with ': '打开方式 ',
    'Create new environment': '新建环境',
    'New environment name': '新环境名称',
    'Overwrite existing environment': '覆盖现有环境',
    'Remove environment': '移除环境',
    'Backup Environment': '备份环境',
    'Import Environment': '导入环境',
    'Import New Environment': '导入新环境',
    'Download environment file': '下载环境文件',
    'Choose location to save the environment file': '选择环境文件的保存位置',
    'Clone from environment: ': '克隆自环境：',
    'Create new environment for ': '新建环境，基于 ',
    'Environment is no longer available:<br>- ': '环境已不可用：<br>- ',
    'Local drive': '本地磁盘',
    'Default environment is updated': '默认环境已更新',

    # ===== Conda 包管理器 =====
    'Conda Package Manager': 'Conda 包管理器',
    'Install Packages': '安装包',
    'Remove Packages': '移除包',
    'Update Packages': '更新包',
    'Update index...': '更新索引…',
    'Update channels': '更新频道',
    'Apply': '应用',
    'Clear': '清除',
    'Mark for installation': '标记为安装',
    'Mark for update': '标记为更新',
    'Mark for removal': '标记为移除',
    'Unmark': '取消标记',
    ' packages available ': ' 个包可用 ',
    '0 packages available ': '0 个包可用 ',
    '1 package available ': '1 个包可用 ',
    'Configure Conda': '配置 Conda',
    'Configure Navigator': '配置导航器',
    'Conda settings (.condarc)': 'Conda 设置（.condarc）',
    'Navigator settings (anaconda-navigator.ini)': '导航器设置（anaconda-navigator.ini）',
    'Manage channels you want Navigator to include.': '管理希望导航器包含的频道。',
    'Channel cannot be empty.': '频道不能为空。',
    'Certificate to verify SSL connections': '用于验证 SSL 连接的证书',
    'Select a repository:': '选择仓库：',
    'Connect to a Repository': '连接到仓库',
    'Connect': '连接',
    'Reset to defaults': '恢复默认',
    'Save and Restart': '保存并重启',

    # ===== 通用按钮 / 对话 =====
    'Ok': '确定',
    'OK': '确定',
    'Cancel': '取消',
    'Yes': '是',
    'No': '否',
    'Close': '关闭',
    'Continue': '继续',
    'Quit': '退出',
    'Copy': '复制',
    'Copy text': '复制文本',
    'Apply changes': '应用更改',
    'Add...': '添加…',
    'Browse...': '浏览…',
    'Learn more': '了解更多',
    'Report Issue': '报告问题',
    'Preferences': '首选项',
    'Title': '标题',
    'next >': '下一页 >',
    '< prev': '< 上一页',
    'Quit Anaconda Navigator?': '退出 Anaconda 导航器？',
    'Quit application': '退出应用',
    'Anaconda Navigator is still busy.<br><br>Do you want to quit?':
        'Anaconda 导航器仍在忙。<br><br>确定要退出吗？',
    'Conda is still busy.\n\nDo you want to cancel the process?':
        'Conda 仍在忙。\n\n要取消该进程吗？',
    'Cancel Process': '取消进程',
    'Close running applications': '关闭正在运行的应用',
    'There are some applications running. Please select \nthe applications you want to close on quit:':
        '有应用正在运行。请选择退出时要关闭的应用：',
    'Proceed with the following actions?': '是否继续执行以下操作？',
    'Do not show again': '不再显示',
    "Don't show again": '不再显示',
    "No, don't show again": '否，且不再显示',
    'No, remind me later': '否，稍后提醒',
    'Continue to Navigator': '继续进入导航器',
    'Offline Mode': '离线模式',

    # ===== 日志查看器 =====
    'Log Viewer': '日志查看器',
    'Select log file:': '选择日志文件：',

    # ===== 登录 / 云端 =====
    'Username:': '用户名：',
    'Password:': '密码：',
    'Sign In': '登录',
    'Sign Up': '注册',
    'Sign in to Anaconda Cloud': '登录 Anaconda 云端',
    "Don’t have an account? ": '还没有账号？ ',
    "Don't have an account? ": '还没有账号？ ',
    "Don't have an account?": '还没有账号？',
    'Login Error': '登录错误',
    'Login failed': '登录失败',
    'Email not verified': '邮箱未验证',
    'Your email is not verified. Please verify it on anaconda.org and log into your account again.':
        '你的邮箱尚未验证。请在 anaconda.org 完成验证后重新登录。',
    'Unexpected login outcome': '意外的登录结果',
    'Anaconda.org login did not produce credentials.': 'Anaconda.org 登录未返回凭据。',
    'SSO login did not produce a token. Check PSM OIDC and API key endpoints.':
        'SSO 登录未获取到令牌。请检查 PSM OIDC 与 API key 端点。',
    'OAuth not supported on this server. Use username/password.':
        '此服务器不支持 OAuth，请使用用户名/密码登录。',
    'Terms of Services & Privacy Policy Update': '服务条款与隐私政策更新',
    'If you do not wish to accept, you will have no access and can close the app.':
        '若不同意，你将无法使用，可以关闭本应用。',
    'You are in offline mode, cloud options are disabled':
        '你处于离线模式，云端功能已禁用',
    'Select environment from Cloud:': '从云端选择环境：',

    # ===== 错误 / 提示 =====
    'Anaconda error': 'Anaconda 错误',
    'Anaconda warning': 'Anaconda 警告',
    'Navigator Start Error': '导航器启动错误',
    'Application launch error': '应用启动错误',
    'Conda process error': 'Conda 进程错误',
    'The following errors occurred:': '发生以下错误：',
    'Unsatisfiable package specifications:': '无法满足的包规格：',
    'The following specifications were found to be in conflict:':
        '发现以下规格相互冲突：',
    'Package not available in offline mode': '离线模式下该包不可用',
    'Broken Anaconda configuration': 'Anaconda 配置损坏',
    'Broken Conda configuration': 'Conda 配置损坏',
    'Broken Navigator configuration': '导航器配置损坏',
    'Navigator Settings Save Error': '导航器设置保存错误',
    'Conda Settings Save Error': 'Conda 设置保存错误',
    'Conflicting preferences in navigator configuration': '导航器配置中存在冲突的首选项',
    'Failed to write user configuration file.': '写入用户配置文件失败。',
    'Please submit a bug report.': '请提交错误报告。',
    'The saved data is not a valid yaml config! Please fix.':
        '保存的数据不是合法的 YAML 配置，请修正。',
    'Warning: File contains no section headers.': '警告：文件不含任何节标题。',
    'There is an instance of Anaconda Navigator already running.':
        '已有一个 Anaconda 导航器实例在运行。',
    'At least one channel should be added to <b>default_channels</b>! Please add...':
        '至少要在 <b>default_channels</b> 中添加一个频道！请添加…',
    'The Anaconda.org API domain is not specified. Set it in Preferences.':
        '未指定 Anaconda.org API 域名，请在首选项中设置。',
    'API domain is not configured': '未配置 API 域名',
    'Anaconda.org API URL is not configured': '未配置 Anaconda.org API 地址',
    'Not installed': '未安装',
    'Installed': '已安装',
    'Updatable': '可更新',

    # ===== 环境文件 / 导入导出 =====
    'Environment File Downloaded': '环境文件已下载',
    'Environment backed up successfully': '环境备份成功',
    'Invalid conda environment file.': '无效的 conda 环境文件。',
    'Environment file "': '环境文件 "',
    '" downloaded to ': '" 已下载到 ',

    # ===== 侧栏（config/preferences.py:61-72 SIDEBAR_LINKS / SIDEBAR_SOCIALS）=====
    # 'Documentation' 已在上面「通用按钮对话」段收过（→ 文档），此处不重复。
    'Anaconda Blog': 'Anaconda 博客',
    # 社交名是品牌名，保留原文（Twitter/Github/Youtube/Linkedin）

    # ===== 内容卡片按钮（widgets/lists/content.py:314-322 valid_tags）=====
    'Read': '阅读',
    'Explore': '探索',
    'Learn More': '了解更多',
    'View': '查看',
    'Engage': '参与',

    # ===== 登录态（widgets/main_window/account_components.py:203-205）=====
    # 注意：源码是 'Connected to ' 后面拼 '<a ...>品牌</a>'，整串先拼接再 setText，
    # 所以落不到这里的键（已在 zhcn_boot._PATTERN_SPECS 用 'Connected to ([\s\S]*)'
    # 正则处理）。这两条键保留是为兼容只传前缀的写法，不参与主路径。
    'Connected to ': '已连接到 ',
    'Partially connected to ': '部分连接到 ',
    'connected as ': '已登录为 ',
    'connected': '已连接',

    # ===== 品牌枚举（config/__init__.py:31-38 AnacondaBrand）=====
    # account_components.py:186-187 把 brand 值直接拼进登录态链接的可见文字，
    # 所以这几个品牌串也要进表，否则会显示「已连接到 Cloud」这种半英文。
    'Cloud': '云端',
    'Enterprise 4 Repository': '企业版 4 仓库',
    'Package Security Manager On-prem': '包安全管理器（本地部署）',
    'Package Security Manager Cloud': '包安全管理器（云端）',

    # ===== 首页工具条介词（widgets/tabs/home.py:175 LabelHome('on')）=====
    # 布局是「[筛选] on [环境] [频道]」，即「所有应用 于 base」。
    # 风险提示：只做整串精确匹配，因此只有恰好等于 'on' 的文案会被替换；
    # 环境名/包名走的是 data 而非文本入口，不受影响。
    'on': '于',
}
