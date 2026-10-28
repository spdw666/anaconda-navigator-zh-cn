# Anaconda Navigator 简体中文运行时汉化

在独立启动器中翻译 Navigator 界面文案，不修改 `anaconda_navigator` 安装包源码。
另提供 Windows 快捷方式安装/还原、PyCharm 检测修复及 JupyterLab 官方语言包的配置工具。

## 已验证环境

| 项目 | 本地完整回归环境 |
|---|---|
| 操作系统 | Windows 11 |
| Navigator | 2.7.1 |
| Python | 3.14.6（Anaconda 自带） |
| Qt | PySide6 6.11.0、qtpy 2.4.3 |
| JupyterLab | 4.5.9，中文语言包 4.5.post3 |

GitHub Actions 在独立 Windows 环境运行完整回归。其它版本和平台应先运行自检；
外挂目录未被 conda 覆盖，不代表任意未来的 Qt/Navigator 升级都兼容。

## 1. 下载与安装

### 下载源码

```powershell
git clone https://github.com/spdw666/anaconda-navigator-zh-cn.git D:\AnacondaHanhua
```

也可使用 GitHub 的 **Code → Download ZIP**，解压到固定目录。
移动目录后重新运行快捷方式安装命令。以下路径仅是示例；脚本按自身位置定位汉化文件。

### 指定 Anaconda 安装目录并自检

在 PowerShell 中执行，修改变量为实际路径：

```powershell
$Anaconda = 'D:\anaconda3'
$Patch = 'D:\AnacondaHanhua'
& "$Anaconda\python.exe" "$Patch\_verify_patch.py"
if ($LASTEXITCODE -ne 0) { throw '汉化自检未通过' }
```

测试使用 `offscreen` Qt，不显示桌面窗口。结果包含被测引擎的绝对路径、SHA-256、
原 38 项语义断言和新增回归。缺依赖导致跳过项时不算完整通过。
完整测试需要该 Anaconda 中的 Navigator、PySide6、JupyterLab 和 json5。

### 安装桌面与开始菜单入口

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$Patch\manage_shortcuts.ps1" `
  -Action Install -AnacondaRoot $Anaconda
if ($LASTEXITCODE -ne 0) { throw '快捷方式安装未完成' }
```

也可执行：

```powershell
& "$Patch\安装汉化.cmd" -AnacondaRoot $Anaconda
```

安装器读取 Windows 的实际桌面/开始菜单位置，支持重定向桌面和带空格路径，
先备份已有入口，再创建并读回校验目标、参数、工作目录和图标。
备份在汉化目录下的 `shortcut_backup`，不上传 GitHub。
已有 `desktop_Anaconda Navigator.lnk`、`startmenu_Anaconda Navigator.lnk` 备份保持兼容。

安装后双击 **Anaconda Navigator**。已运行的旧进程不会热更新，正常退出再启动才加载新代码。

### 不安装快捷方式，直接启动

```powershell
& "$Anaconda\pythonw.exe" "$Anaconda\cwp.py" $Anaconda `
  "$Anaconda\pythonw.exe" "$Patch\launch_zh.py"
```

通过 `cwp.py` 配置 Anaconda 的 DLL/PATH 环境。已收录文案包括主页/环境/学习/社区、
菜单、包管理提示、对话框，以及已盘点的应用介绍、课程标题、摘要、内容按钮和分类图片。
具体覆盖与保留数据见下文；云端新增内容可用独立审计命令检查。

## 2. 还原英文与迁移

```powershell
& "$Patch\还原英文.cmd" -AnacondaRoot $Anaconda
```

或：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$Patch\manage_shortcuts.ps1" `
  -Action Restore -AnacondaRoot $Anaconda
```

两个入口均会处理：有有效备份时恢复备份；缺少备份时根据已验证的 Anaconda 根目录
生成官方英文入口。开始菜单与桌面采用相同兜底，不跳过某个入口后报告全部完成。
根目录也可从已有快捷方式识别；新安装或迁移时显式传入 `-AnacondaRoot` 最明确。

等命令退出码为 `0`、入口读回校验完成，并正常关闭已有 Navigator 进程后，再移除汉化目录。
该操作只还原 Navigator 入口，不撤销 PyCharm 路径或 JupyterLab 语言设置。

## 3. 翻译与数据分离

引擎按字段语义区分界面文案与逻辑数据，当前资源包括：

| 资源 | 覆盖内容 |
|---|---|
| 基础词条 216 条 + 补充词条 164 条 | 导航、菜单、设置、登录、导入/备份、包管理、提示和对话框 |
| 动态规则 46 条 | 启动/安装/更新/移除、环境操作、下载、账号计数、路径提示等 |
| 公共内容词条 265 条 | 应用说明、课程/文档/社区标题与摘要、访问按钮及保留的产品名 |
| 官方 QtBase 中文词条 1,785 条 | Qt 原生消息框、文件选择框、编辑菜单等，保留 Qt 上下文和占位符 |
| 本地中文 SVG 10 张 | 课程、学习路径、认证等分类图与已识别的快速起步侧栏图片 |

公共内容使用完整显示字段匹配；富文本只改文字节点，不改标签、属性或链接。
中文搜索同时匹配原文及译文，保留原类别筛选行为。

- **实际输入保持原文**：不包装 QLineEdit/QTextEdit 等的内容 `setText`，placeholder、tooltip 可翻译。
- **环境名保持原文**：通用组合框、首页环境组合框、环境名按钮及其自绘菜单不翻译数据。
- **应用筛选限定控件**：只翻译 Navigator `ComboHomeFilter` 的四组固定 label/data 配对；
  `userData` 不变，程序化 `setCurrentText` 与中文标签同步。
- **包状态筛选只改显示**：显示“已安装/未安装/可更新/已选择/全部”；
  `currentText()`、项目数据与状态查表键仍为 `Installed / Not installed / Updatable / Selected / All`。
- **文件筛选只改显示**：翻译人类可读标签，保留 `*.yaml` 等模式；返回原始所选筛选值，
  使 Navigator 的 YAML 扩展名判断仍使用原键。
- **内容与图片只改显示**：应用 ID、元数据标题/摘要原值、URI、图片源、跳转目标及点击行为不变。
- **保留产品与技术标识**：Anaconda、PyCharm、JupyterLab、Conda-Forge 等品牌，Python/SQL/AI 等术语，
  包名、版本、环境名、账号名、路径、URL 与原始诊断数据不作为普通 UI 文案改写。
- **方法安装是事务**：安装失败撤销已替换方法；`uninstall()` 恢复原属性及继承关系。
- **无控制台也能回退**：`pythonw.exe` 缺少 stderr 时，诊断输出不阻断官方英文入口。

精确匹配不等于数据类型识别。例如合法环境名 `Home` 也会命中词条；
必须先识别控件和字段语义，再决定是否翻译。

## 4. PyCharm 已安装但 Navigator 显示“安装”

自定义安装目录未被发现时执行：

```powershell
& "$Anaconda\python.exe" "$Patch\fix_pycharm.py" 'E:\JetBrains\PyCharm'
```

不传安装路径则自动发现。脚本验证 `product-info.json` 和 `bin\pycharm64.exe`，
归一为绝对目录，再按产品代码写入 Navigator `[applications]`：

| productCode | 配置键 |
|---|---|
| PY | pycharm_pro_path |
| PC / PE | pycharm_ce_path |

只修改目标段，保留其它配置和换行；修改前备份，原子写入，重复执行不重写。
`--config` 可指定待修复 INI。检测规则匹配产品元数据，不是目录名称。

## 5. JupyterLab 官方简体中文

JupyterLab 的官方语言包不依赖 Navigator Qt 补丁。先在运行 JupyterLab 的同一环境安装：

```powershell
& "$Anaconda\python.exe" -m pip install jupyterlab-language-pack-zh-CN
```

然后在 JupyterLab **Settings → Language → Simplified Chinese** 切换并刷新。
见 [JupyterLab 官方语言说明](https://jupyterlab.readthedocs.io/en/stable/user/language.html)。

也可后台写入正确的翻译插件设置：

```powershell
& "$Anaconda\python.exe" "$Patch\configure_jupyterlab.py" --locale zh_CN
```

工具遵循 JupyterLab 实际 user-settings 目录（包括 `JUPYTERLAB_SETTINGS_DIR`），
更新 `@jupyterlab/translation-extension/plugin.jupyterlab-settings` 的 `locale`，保留其它设置，
首次修改前保存字节级 `.bak_zhcn` 备份。支持 JSON5 输入；修改后序列化为 JSON，注释保留在备份。

旧说明中的顶层 `jupyter_config.json → {"Language":"zh_CN"}` **不是界面语言配置**。
如果曾按旧说明操作，可同时只移除旧键：

```powershell
& "$Anaconda\python.exe" "$Patch\configure_jupyterlab.py" --locale zh_CN --clean-legacy-language
```

`--dry-run` 仅报告拟变更；`--settings-dir`、`--legacy-config` 可指定配置以便隔离验证。
语言包版本不同可能导致新文案未覆盖，应以实际界面和语言包发布记录判断。

## 6. Spyder

Spyder 自带中文资源与本项目无关。在带有中文资源的 Spyder 中，从
`Tools → Preferences → Application → Advanced settings → Language` 选简体中文后重启。

## 7. 文件与验证

| 文件 | 用途 |
|---|---|
| nav_zh_dict.py / zhcn_boot.py | 词表与事务式 Qt 文案补丁 |
| nav_content.py / content_zh.json / ui_zh_extra.json | 语义限定的内容、原生 Qt、文件筛选与中文搜索 |
| nav_assets.py / assets/zh_cn/ | 已识别的官方分类与侧栏图片的中文显示资源 |
| assets/qttranslations/ | 固定版本的官方 QtBase 资源、上游许可证和来源哈希 |
| coverage_audit.py / coverage_catalog.json | 独立公共内容快照审计及当前缓存的新增英文检测 |
| launch_zh.py | 中文启动器，失败进入官方英文入口 |
| manage_shortcuts.ps1 | 快捷方式安装、备份、还原及读回验证 |
| 安装汉化.cmd / 还原英文.cmd | 对应 PowerShell 操作封装 |
| fix_pycharm.py | 校验安装目录、限定 INI 段修复探测路径 |
| configure_jupyterlab.py | 官方翻译插件 locale 配置 |
| _verify_patch.py / tests/ | 当前源码副本的完整回归 |
| trace-sample.log | 早期版本历史运行样本，不代表当前覆盖率 |

```powershell
& "$Anaconda\python.exe" "$Patch\_verify_patch.py"
$LASTEXITCODE
```

覆盖：原 38 项语义、环境名撞词/粘贴、真实 Navigator 控件、Qt 重载、幂等安装/完整撤销、
53 个安装阶段的前后故障注入、真实 pythonw、跨工作目录的被测对象定位、配置段与路径、真实 Windows COM
快捷方式夹具，以及 JupyterLab 原生 locale 解析。配置和快捷方式测试仅写入临时目录。

当前完整套件为 **85 项，零跳过**，包含独立输入快照、原生卡片、摘要悬浮层、中文搜索、
分类图片、文件筛选逻辑、包筛选绘制、动态消息及用户数据保持测试。
测试在临时用户目录中运行，不写真实 Navigator 或 Jupyter 配置。

### 公共内容覆盖审计

```powershell
# 仓库中独立的已盘点快照，不读取真实用户配置
& "$Anaconda\python.exe" "$Patch\coverage_audit.py" --report "$env:TEMP\navigator-coverage.json"

# 可选：同时检查当前 Navigator 下载的公共内容缓存
& "$Anaconda\python.exe" "$Patch\coverage_audit.py" `
  --live-content "$env:APPDATA\.anaconda\navigator\content\content.json" `
  --report "$env:TEMP\navigator-live-coverage.json"
```

`coverage_catalog.json` 的 2026-10-28 快照包含内置 51 条及当时缓存 99 条内容
（合计 104 个不同标题、99 个不同摘要）、28 个内置应用定义、32 个远端应用定义及 6 个 conda 应用。
独立审计 528 个显示字段：495 个翻译字段、33 个重复出现的产品名字段，未收录为 0。
加入当时 99 条实时缓存后，共 778 个字段，未收录仍为 0。
产品名称计入已明确保留，不以“任何英文都必须消失”作为通过标准。
审计遇到未收录的新英文标题、摘要或按钮会返回非零退出码并列入 `missing`；
仓库快照通过不代表未来云端新增内容已覆盖。

另以相同公共输入在补丁前后分别回放原生主页、学习、社区、环境及消息/文件对话框：
主页 15 条应用说明、学习 82 条、社区 17 条内容和 54 张训练分类图已核对。
该页面回放使用隔离配置、真实 Navigator 控件及受控网络/API 输入；
它不等同于用户正在运行的完整 MainWindow 的所有交互逐项实测。

补词条后完整自检，并检查新词是否可能是用户数据。
设置 `ANACONDA_ZH_TRACE` 可记录去重后的实际翻译命中；诊断日志不上传仓库。

## 资源来源与许可证

项目代码遵循根目录 `LICENSE`。本地中文分类和侧栏 SVG 由项目生成，
分类图保留原有 Anaconda 品牌图形；产品商标与品牌权利归各自权利人。

Qt 原生翻译来自 [Qt 官方 qttranslations](https://github.com/qt/qttranslations)，
固定为 Qt 6.11 分支提交 `41b114145cefe539177ebafe7758a2d287123ac8` 的原始 `qtbase_zh_CN.ts`。
本项目通过上下文匹配读取有效译文，不修改该上游文件，不把未完成或占位符不符的译文装入运行时。
上游资源适用自己的许可证，根目录项目许可不覆盖它；
参阅 `assets/qttranslations/NOTICE.txt`、`licenseRule.json`、许可证全文和 `UPSTREAM.json` 中的来源与 SHA-256。

## 项目说明

早期检索未发现满足当时需求的现成 Navigator 补丁，因此采用外挂实现；
这是当次检索结果，不代表其它实现不存在。本项目并非 Anaconda 官方项目。
源码未改只证明磁盘文件未变，运行期补丁兼容性仍以测试和实际使用结果为准。
