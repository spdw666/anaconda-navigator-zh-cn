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
| `nav_zh_dict.py` | 词条表，201 条界面文案（英文原文 → 中文译文） |
| `zhcn_boot.py` | 汉化引擎，给 Qt 类方法打补丁 + 拼接型文案的正则规则 |
| `launch_zh.py` | 启动器，先装补丁再走官方入口 |
| `_verify_patch.py` | 自检套件，38 项断言（离线，不需要开 GUI） |
| `还原英文.cmd` | 双击即还原英文界面 |

---

## 三、已生效的内容

### 1. Anaconda Navigator —— 桌面快捷方式已改指向汉化入口

桌面 `Anaconda Navigator.lnk` 现指向：
```
D:\anaconda3\pythonw.exe D:\anaconda3\cwp.py D:\anaconda3 D:\anaconda3\pythonw.exe D:\AnacondaHanhua\launch_zh.py
```
开始菜单同名快捷方式同步修改。两者原版都备份为 `*.lnk.bak_zhcn`。

**实测效果**（真机 GUI 启动，运行期翻译溯源 38 条命中）：

| 位置 | 原文 | 显示 |
|---|---|---|
| 窗口标题 | Anaconda Navigator | Anaconda 导航器 |
| 顶部标签 | Home / Environments / Learning / Community | 主页 / 环境 / 学习 / 社区 |
| 文件菜单 | &Preferences / &Restart / &Quit | &首选项 / &重启 / &退出 |
| 帮助菜单 | &Online Documentation / &Logs viewer / &About | &在线文档 / &日志查看器 / &关于 |
| 首页筛选 | All applications / Installed applications / Not installed applications / Updatable applications | 所有应用 / 已安装应用 / 未安装应用 / 可更新应用 |
| 应用按钮 | Install / Launch / Update Now | 安装 / 启动 / 立即更新 |
| 环境页 | Create / Clone / Import / Backup / Remove | 创建 / 克隆 / 导入 / 备份 / 移除 |
| 搜索框 | Search Environments / Search Packages | 搜索环境 / 搜索包 |
| 包管理器 | Conda Package Manager / Apply / Clear | Conda 包管理器 / 应用 / 清除 |
| 状态栏 | 575 packages available | 575 个包可用 |
| 对话框 | Ok / Cancel / Yes / No / Copy text / Learn more / Report Issue | 确定 / 取消 / 是 / 否 / 复制文本 / 了解更多 / 报告问题 |

### 2. JupyterLab —— 官方简体中文语言包已安装并启用

- 安装包：`jupyterlab-language-pack-zh-CN 4.5.post3`（来源 https://github.com/jupyterlab/language-packs）
- 配置：`C:\Users\ms\.jupyter\jupyter_config.json` → `{"Language": "zh_CN"}`
- 语言包目录 17 个 `.mo`，覆盖 jupyterlab 本体与常用扩展

### 3. Spyder —— 自带官方中文，一行设置即可

Spyder 6.1.5 已自带 `spyder\locale\zh_CN\LC_MESSAGES\spyder.mo`（195 KB），**不需要任何汉化包**：
菜单 `Tools → Preferences → Application → Advanced settings → Language` 选「简体中文」→ 重启。

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
- `OSError: Could not find a suitable TLS CA certificate bundle, invalid path: D:\anaconda3\Lib\site-packages\certifi\cacert.pem`
- `QFontDatabase: Cannot find font directory D:/anaconda3/Library/lib/fonts`（offscreen 模式下出现）

这些是这台机器 Anaconda 环境自身的问题（certifi 证书缺失最值得修），不影响界面汉化。
