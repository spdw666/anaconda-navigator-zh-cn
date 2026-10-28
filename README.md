# Anaconda 简体中文汉化包（Navigator + JupyterLab）

> 状态：**已生效**（2026-10-28）
> 汉化目录：`D:\AnacondaHanhua`　Anaconda 安装目录：`D:\anaconda3`
>
> **路径约定**：本文所有路径以 `D:\anaconda3`（Anaconda 安装目录）和 `D:\AnacondaHanhua`（本汉化包目录）
> 为例。装到别处时，把这两个前缀换成你自己的实际路径即可 —— 本汉化包内部**不硬编码任何路径**
> （`launch_zh.py` 按自身位置定位）。

---

## 一、结论先说

**Anaconda Navigator 官方没有中文版**，GitHub / Gitee / CSDN / V2EX 全网都不存在可下载的汉化包（详见第六节检索记录）。
原因很直接：Navigator 用的是 PySide6 (Qt) 原生控件，**源码里没有任何 i18n / gettext / .mo 机制**
（`anaconda_navigator` 2.7.1 全包 0 个 `.mo`、0 个 `.po`、0 处 `gettext.install`）。

所以本汉化包的做法是：**外挂式运行时翻译引擎**——
不改 `anaconda_navigator` 一行源码（实测 448 个文件哈希与 pip RECORD **全部一致**），
而是在启动时给 Qt 的文本入口方法打补丁，命中词表即替换成中文。

好处：conda 升级 / 重装 Anaconda 都不会破坏汉化包本体，也可一键还原英文。

---

## 二、文件清单

| 文件 | 作用 |
|---|---|
| `nav_zh_dict.py` | 词条表，216 条界面文案（英文原文 → 中文译文） |
| `zhcn_boot.py` | 汉化引擎，给 Qt 类方法打补丁 + 28 条拼接型文案的正则规则 |
| `launch_zh.py` | 启动器，先装补丁再走官方入口 |
| `_verify_patch.py` | 自检套件，38 项断言（离线，不需要开 GUI） |
| `fix_pycharm.py` | 修「PyCharm 已装但 Navigator 显示未安装」（见第三节第 4 小节） |
| `还原英文.cmd` | 双击即还原英文界面 |

---

## 三、已生效的内容

### 1. Anaconda Navigator —— 桌面快捷方式已改指向汉化入口

桌面 `Anaconda Navigator.lnk` 现指向：
```
D:\anaconda3\pythonw.exe D:\anaconda3\cwp.py D:\anaconda3 D:\anaconda3\pythonw.exe D:\AnacondaHanhua\launch_zh.py
```
开始菜单同名快捷方式同步修改。两者原版都备份为 `*.lnk.bak_zhcn`。

**实测效果**（真机 GUI 启动，运行期翻译溯源 51 条命中，完整清单见 `trace-sample.log`）：

| 位置 | 原文 | 显示 |
|---|---|---|
| 窗口标题 | Anaconda Navigator | Anaconda 导航器 |
| 顶部标签 | Home / Environments / Learning / Community | 主页 / 环境 / 学习 / 社区 |
| 文件菜单 | &Preferences / &Restart / &Quit | &首选项 / &重启 / &退出 |
| 帮助菜单 | &Online Documentation / &Logs viewer / &About | &在线文档 / &日志查看器 / &关于 |
| 首页筛选 | All applications / Installed applications / Not installed applications / Updatable applications | 所有应用 / 已安装应用 / 未安装应用 / 可更新应用 |
| 应用按钮 | Install / Launch / Update Now | 安装 / 启动 / 立即更新 |
| 应用卡片提示 | Version 4.6.4 available | 可更新到 4.6.4 |
| 环境页 | Create / Clone / Import / Backup / Remove | 创建 / 克隆 / 导入 / 备份 / 移除 |
| 搜索框 | Search Environments / Search Packages | 搜索环境 / 搜索包 |
| 包管理器 | Conda Package Manager / Apply / Clear | Conda 包管理器 / 应用 / 清除 |
| 状态栏 | 575 packages available | 575 个包可用 |
| 账号状态 | Connected to Cloud | 已连接到 云端 |
| 对话框 | Ok / Cancel / Yes / No / Copy text / Learn more / Report Issue | 确定 / 取消 / 是 / 否 / 复制文本 / 了解更多 / 报告问题 |
| 更新提示 | There's a new version of Anaconda Navigator available... | Anaconda 导航器有新版本可用，强烈建议更新… |

### 2. JupyterLab —— 官方简体中文语言包已安装并启用

- 安装包：`jupyterlab-language-pack-zh-CN 4.5.post3`（来源 https://github.com/jupyterlab/language-packs）
- 配置：`C:\Users\ms\.jupyter\jupyter_config.json` → `{"Language": "zh_CN"}`
- 语言包目录 17 个 `.mo`，覆盖 jupyterlab 本体与常用扩展

**关于首页卡片那个 `↗ 4.5.9`**：它是「有新版可升」的标记，不是待办、不是出错。
证据链：`widgets/lists/apps.py:335-338`（`self.version != self.versions[-1] and self.installed`
→ `setProperty('pressed', True)` + `setToolTip('Version 4.6.4 available')`）、
`light.css:909-911`（`ButtonApplicationVersion[pressed="true"]` 给
`qproperty-icon: update-app-active.svg` + `color: #00A3E0`）、
图标本身 `static/images/common/icons/update-app-active.svg` 就是一个蓝色斜箭头。
**`4.5.9` 是当前已装版本，可升到的版本在鼠标提示里。**

本机实测可升目标：jupyterlab `4.5.9 → 4.6.4`、notebook `7.5.7 → 7.6.3`、
anaconda-navigator `2.7.1 → 2.7.3`（就是右上角那个绿色「立即更新」按钮，
判据在 `widgets/main_window/__init__.py:711`）。

**本机决定：不升。** 理由：`zh-CN` 语言包最新 tag 只有 `zh-CN@v4.5.post3`（2026-04-13），
4.6 系列尚未发布。语言包走 gettext 目录（`jupyterlab_server/translation_utils.py:152`
用 `entry_points(group="jupyterlab.languagepack")` 注册，**不校验版本**），升到 4.6.4 后
4.5.post3 仍会加载、老词条照旧中文，但 4.6 新增的字符串会回落到英文——
当前 4.5.9 + 4.5.post3 已是最完整的中文组合，没必要动。

### 3. Spyder —— 自带官方中文，一行设置即可

Spyder 6.1.5 已自带 `spyder\locale\zh_CN\LC_MESSAGES\spyder.mo`（195 KB），**不需要任何汉化包**：
菜单 `Tools → Preferences → Application → Advanced settings → Language` 选「简体中文」→ 重启。

### 4. PyCharm —— 已修好「装了却显示未安装」

**现象**：PyCharm 装在 `D:\PyCharm 2025.3.4` 并能正常用，但 Navigator 首页卡片一直显示「安装」按钮。

**原因**（读 `anaconda_navigator` 源码确认，不是猜的）：Navigator 的 JetBrains 探测器
（`api/external_apps/bundle/jetbrains_utils.py:499-548`）只在四个固定根目录下找：
```
C:\Program Files\JetBrains
C:\Program Files (x86)\JetBrains
%LOCALAPPDATA%\Programs
%LOCALAPPDATA%\JetBrains\Toolbox\apps
```
另外两条兜底（PATH、注册表 `HKEY_CLASSES_ROOT\Applications\pycharm64.exe\...`）本机也都没有。
装在 D 盘根目录 → 四条路径全不命中 → `is_installed` 恒为 False。

**修法**（不改任何源码，只写配置）：Navigator 的探测器第一步是 `CheckConfiguredRoots()`，
读 `anaconda-navigator.ini` 的 `[applications]` 段 `<app_name>_path`。把路径填进去即可：

```ini
[applications]
pycharm_pro_path = D:\PyCharm 2025.3.4
```

`fix_pycharm.py` 自动做这件事（自动找安装目录、读 `product-info.json` 判断专业版/社区版、
逐行替换保留 CRLF、自动备份）：

```
D:\anaconda3\python.exe D:\AnacondaHanhua\fix_pycharm.py
```

**注意 productCode 必须对上**（`base_apps.yml`）：

| 版本 | productCode | 配置键 |
|---|---|---|
| 专业版 | `PY` | `pycharm_pro_path` |
| 社区版 / 教育版 | `PC` / `PE` | `pycharm_ce_path` |

填错键没用（实测：把专业版路径写进 `pycharm_ce_path` 仍然显示未安装，因为版本校验
`data['productCode'] in self.__product_code` 不通过）。

**实测效果**：卡片显示版本 `2025.3.6.1`，按钮从「安装」变成「启动」。

---

## 四、怎么用

**正常启动**：双击桌面「Anaconda Navigator」即可，自动中文。

**想临时看英文**（不改快捷方式）：
```
D:\anaconda3\pythonw.exe D:\anaconda3\cwp.py D:\anaconda3 D:\anaconda3\pythonw.exe D:\anaconda3\Scripts\anaconda-navigator-script.py
```

**彻底还原英文**：双击 `D:\AnacondaHanhua\还原英文.cmd`。

**自检汉化引擎是否正常**：
```
D:\anaconda3\python.exe D:\AnacondaHanhua\_verify_patch.py
```
预期最后一行 `=== ALL 38 CHECKS PASSED ===`。

**PyCharm 显示未安装**：跑一次 `fix_pycharm.py`（见第三节第 4 小节），然后重启 Navigator。

---

## 五、补词条的方法

遇到没翻到的英文，打开 `nav_zh_dict.py`，在 `ZH = {` 里加一行：

```python
    'Your English Text': '你的中文译文',
```

保存后重启 Navigator 即生效（无需重新打包）。

**必须逐字节一致**：键要包含原文的首尾空格和 HTML 标签，例如状态栏那条是
`' packages available ': ' 个包可用 '`（原文前后各有一个空格）。

拼接型文案（带变量）在 `zhcn_boot.py` 的 `_PATTERN_SPECS` 里加正则，例如
`(r'Loading packages of <b>(.*?)</b>', '正在加载包：<b>\\1</b>')`。

---

## 六、为什么没有直接用现成汉化包（检索记录）

| 检索面 | 关键词 / 位置 | 结果 |
|---|---|---|
| GitHub 仓库搜索 | `Anaconda 汉化`、`anaconda chinese patch`、`anaconda navigator zh`、`Anaconda Navigator 中文版`、`conda GUI chinese` | 命中的全是 star=0 的「安装包+图文教程」仓库，**无汉化补丁代码** |
| Gitee API | `anaconda 汉化`、`anaconda navigator 汉化`、`navigator 中文`、`anaconda 中文` | 全部 0 条 |
| V2EX | 帖 1083259「求问，Anaconda3，导航器，怎么汉化？」 | 19 楼唯一实质回复：「可以，修改 anaconda-navigator 这个 python 包里面的代码」 |
| CSDN / php.cn / cr173 | 相关问答与教程页 | 只有安装教程，无可下载补丁 |
| 唯一真实存在的「Anaconda 系组件汉化包」 | `heyuesong/spyder-`、`QiumeiChu/spyder_simplified_chinese` | 只针对 **Spyder**，不针对 Navigator |

---

## 七、安全边界（重要，已实测验证）

`anaconda_navigator\widgets\manager\table.py:295` 用**组合框当前显示文本**查字典：
```python
self._filterbox = C.COMBOBOX_VALUES.get(text)
```
`utils\constants.py:73-84` 里 `COMBOBOX_VALUES_ORDERED = ['Installed', 'Not installed', 'Updatable', 'Selected', 'All']`。

**如果把这些下拉项翻成中文，包过滤会静默失效。** 所以引擎有意遵守以下边界：

1. **`QComboBox.addItems(list)` 与单参数 `addItem` 一律不翻译** —— 保持包状态筛选全英文；
2. **只翻双参数 `addItem(text, userData)`** —— 这类逻辑走 `itemData()`，翻显示文本安全（首页的「所有应用」筛选就属于这类）；
3. **绝不翻译环境名 / 包名 / 频道名 / URL / 路径** —— 词表只收确定的界面文案，且只做整串精确匹配，不做子串替换；
4. 自检套件里专门有 8 项「安全边界」断言守着这些规则（`base`、`numpy`、`pandas`、`scikit-learn`、`pytorch`、`D:\anaconda3\envs\demo`、`https://repo.anaconda.com/pkgs/main` 必须原样透传）。

---

## 八、诊断：想看哪些文案被翻了

设环境变量后启动，每次翻译会追加一行到日志：

```powershell
$env:ANACONDA_ZH_TRACE = "D:\AnacondaHanhua\_trace.txt"
& "D:\anaconda3\pythonw.exe" "D:\anaconda3\cwp.py" "D:\anaconda3" "D:\anaconda3\pythonw.exe" "D:\AnacondaHanhua\launch_zh.py"
```

日志格式：`'Home' => '主页'`。同一词条只记一次。

---

## 九、这台机器上与本汉化无关的既有报错

用**官方原版入口**（不带汉化）启动，同样会看到以下报错，与汉化包无关：

- `TypeError: a bytes-like object is required, not 'str'`（`conda_api/__init__.py:1416`，conda 输出编码不匹配）
- `AttributeError: 'bytes' object has no attribute 'copy'`（`anaconda_api.py:367`）
- `QFontDatabase: Cannot find font directory D:/anaconda3/Library/lib/fonts`（offscreen 模式下出现）

**certifi 证书那条已查清、无需处理**：早先日志里的
`Could not find a suitable TLS CA certificate bundle, invalid path: ...\certifi\cacert.pem`
是 conda 当时正在安装 `certifi` 时的**瞬时竞态**（`conda-meta` 时间戳与本条报错同一秒），
conda 自己已装完。2026-10-28 实测：`cacert.pem` 存在（235863 字节）、`ssl` 加载 118 个 CA、
`requests.get('https://repo.anaconda.com/pkgs/main/')` 返回 200，全部健康。

