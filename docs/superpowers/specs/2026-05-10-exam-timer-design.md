# 公考刷题计时器 设计文档

**日期**：2026-05-10
**状态**：已确认

---

## 一、项目目标

开发一款 Windows 桌面端公考计时器，专用于行测、申论刷题计时。纯本地运行、无联网、无广告。

## 二、技术选型

| 项目 | 选择 | 说明 |
|------|------|------|
| 语言 | Python 3.13 | 当前环境已安装 |
| GUI | PyQt6 | 界面精致，组件丰富，适合悬浮窗 |
| 打包 | PyInstaller | 输出单个 .exe，预计 60-80MB |
| 存储 | JSON 文件 | `%APPDATA%/ExamTimer/` 目录 |
| 全局热键 | ctypes 调 Windows API | `RegisterHotKey` + `UnregisterHotKey` |
| 防锁屏 | ctypes 调 Windows API | `SetThreadExecutionState` |
| Excel 导出 | openpyxl | 轻量级 .xlsx 写入 |

## 三、项目结构

```
ExamTimer/
├── main.py                 # 入口：系统托盘 + 悬浮窗启动
├── timer_engine.py         # 计时状态机（倒计时/正计时）
├── exam_manager.py         # 行测/申论模式 + 模块管理
├── hotkey_manager.py       # 全局快捷键注册/管理
├── data_manager.py         # JSON 读写、历史记录
├── reminder.py             # 提醒弹窗（5/3/1分钟 + 结束）
├── anti_screensaver.py     # 防屏幕锁屏
├── exporter.py             # Excel/CSV 导出
└── ui/
    ├── main_window.py      # 主悬浮窗（置顶/拖拽/缩放/穿透）
    ├── timer_widget.py     # 计时数字 + 进度条
    ├── module_bar.py       # 模块标签 + 切换
    ├── settings_dialog.py  # 设置面板
    ├── history_dialog.py   # 历史/复盘面板
    └── mini_timer.py       # 单题小计时器
```

## 四、核心模块设计

### 4.1 timer_engine.py — 计时引擎

状态机：`IDLE → RUNNING → PAUSED → FINISHED`

- 倒计时模式：从设定时长倒数至 0
- 正计时模式：从 0 开始累加
- QTimer 驱动，每秒 tick
- 信号：`tick(remaining_sec, elapsed_sec)`、`timeout()`、`state_changed(new_state)`

### 4.2 exam_manager.py — 考试模式管理

**行测模式**：
- 一键 120 分钟整卷计时
- 5 个预设模块：常识、言语、数量、判断、资料
- 各模块时长可自定义（默认：常识10min、言语35min、数量15min、判断35min、资料25min）
- 一键切换下一模块（自动记录当前模块用时）
- 模块配置可保存

**申论模式**：
- 一键 150/180 分钟可选
- 小题、大作文分段独立计时

**双轨计时**：整卷计时持续运行 + 模块计时独立追踪

### 4.3 全局快捷键

| 功能 | 默认快捷键 | 说明 |
|------|-----------|------|
| 结束当前模块+切下一模块 | **Space** | 唯一固定键，最频繁操作 |
| 开始/暂停 | Ctrl+Shift+Space | 可自定义 |
| 重置 | Ctrl+Shift+R | 可自定义 |
| 切换行测/申论 | Ctrl+Shift+M | 可自定义 |
| 切换穿透模式 | Ctrl+Shift+T | 可自定义 |
| 切换专注模式 | Ctrl+Shift+F | 可自定义 |

快捷键配置存储在 `config.json`，设置面板中可修改。

### 4.4 数据存储

**目录**：`%APPDATA%/ExamTimer/`

**config.json**：
```json
{
  "hotkeys": { "start_pause": "Ctrl+Shift+Space", ... },
  "appearance": { "theme": "dark", "opacity": 0.9 },
  "reminder": { "enabled": true, "sound": false },
  "xingce_modules": [
    { "name": "常识", "duration_min": 10 },
    { "name": "言语", "duration_min": 35 },
    ...
  ],
  "shenlun_duration": 150
}
```

**history.json**：
```json
[
  {
    "date": "2026-05-10 14:30",
    "mode": "行测",
    "total_elapsed_sec": 7050,
    "modules": [
      { "name": "常识", "planned_min": 10, "actual_sec": 580, "overtime": false },
      ...
    ],
    "questions": [
      { "label": "第3题", "elapsed_sec": 45 }
    ]
  }
]
```

### 4.5 UI 设计

**主悬浮窗**（默认紧凑横条 400×80px）：

```
┌─────────────────────────────────────────────────┐
│ [行测] │ 言语理解 │  28:15  │ ████████░░ │  ⚙  │
└─────────────────────────────────────────────────┘
  模式     当前模块   大数字时间    进度条      设置
```

**自适应缩放**：
- 字体大小 = 窗口高度 × 比例系数（主数字 0.55，标签 0.18）
- 所有元素用 Layout 管理，随窗口拉伸
- resizeEvent 中动态更新字体和内边距
- 支持全屏（字体最大化，适合远距离观看）

**三种窗口模式**：
- 普通模式：可交互，按钮可见
- 穿透模式：鼠标事件穿透到下层窗口（`Qt.WindowTransparentForInput`），纯显示 + 快捷键
- 专注模式：隐藏所有控件，只显示时间数字 + 进度条

**主题**：深色（#1e1e2e 背景 + #cdd6f4 文字）和浅色（#eff1f5 背景 + #4c4f69 文字），护眼配色

**右键菜单**：切换模式、切换穿透、切换专注、设置、历史记录、导出数据、退出

### 4.6 提醒系统

- 剩余 5/3/1 分钟：悬浮窗边框闪烁 3 秒 + 静音弹窗
- 计时结束：弹窗 + 可选提示音
- 提醒开关在设置中独立控制

### 4.7 防锁屏

计时运行期间调用 Windows API：
```python
ctypes.windll.kernel32.SetThreadExecutionState(0x80000003)
# ES_DISPLAY_REQUIRED | ES_SYSTEM_REQUIRED | ES_CONTINUOUS
```
计时停止后恢复正常状态。

### 4.8 数据导出

- Excel (.xlsx)：openpyxl 生成，含日期、模式、整卷用时、各模块用时、超时标记
- CSV (.csv)：纯文本备选，无需额外依赖

## 五、数据流

```
用户操作（按钮/快捷键/空格）
  → exam_manager 处理逻辑
  → timer_engine 更新状态
  → 信号通知 UI 刷新
  → data_manager 记录历史

每秒 tick
  → timer_engine 计算时间
  → reminder 检查阈值
  → UI 更新数字 + 进度条
```

## 六、打包输出

- PyInstaller 打包为单个 `公考计时器.exe`
- 附带 `使用说明.txt`（极简，快捷键清单 + 功能概览）
- 首次运行自动在 `%APPDATA%/ExamTimer/` 创建默认配置和空历史文件
