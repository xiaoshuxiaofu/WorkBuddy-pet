# WorkBuddy Pet 🐾

**WorkBuddy 桌面宠物** — 聊天感知模式，跟随对话状态切换表情动画

生成 Codex 兼容的像素风精灵图集宠物，以透明窗口形式显示在桌面上。宠物会实时反映 AI agent 的工作状态，配合像素风对话气泡和完成提示音。

## 功能特色

- 🎮 **9 种动画状态**：待机、奔跑、挥手、跳跃、失败、等待、审查代码等
- 🧠 **聊天感知模式**：宠物随 AI 对话状态自动切换表情和气泡文字
- 🔔 **完成提示音**：任务完成时播放系统提示音 + OK 按钮
- 🖱️ **拖拽 / 双击 / 右键菜单**：轻松交互
- 🎨 **精灵图集生成**：一键生成像素风宠物图集
- 🔌 **Hooks 自动安装**：首次启动自动注入，开箱即用

## 快速开始

### 方式一：一键启动（推荐）

```bash
python scripts/pet_launch.py
```

首次运行会自动将 hooks 注入到 `~/.workbuddy/settings.json`，后续重启 WorkBuddy 即可通过 hooks 自动触发宠物状态同步。

### 方式二：手动安装 hooks

```bash
# 安装 hooks（幂等，重复运行不会重复添加）
python scripts/install_hooks.py

# 卸载 hooks
python scripts/install_hooks.py --uninstall
```

### 方式三：手动启动（调试用）

```bash
# 启动 daemon
python scripts/pet_daemon.py &

# 启动宠物
python scripts/desktop_pet.py \
  --atlas assets/demo/blue-slime_atlas.png \
  --manifest assets/demo/pet.json \
  --scale 2.0
```

## 聊天感知模式

宠物通过 WorkBuddy hooks 实现状态自动同步：

| 事件 | 宠物状态 | 气泡文字 |
|------|---------|---------|
| `UserPromptSubmit` | waiting | "正在思考..." |
| `PostToolUse` | running | "工作中..." |
| `Stop` | waving | "完成！" + 提示音 |
| `SessionStart` | — | 自动启动 daemon + 宠物 |

也可以手动控制：

```bash
python scripts/pet_bridge.py thinking "正在思考..."
python scripts/pet_bridge.py running "工作中..."
python scripts/pet_bridge.py waving "完成！"
python scripts/pet_bridge.py idle
```

## 操作方式

| 操作 | 方式 |
|------|------|
| 拖拽宠物 | 左键拖拽 |
| 切换状态 | 双击（循环切换） |
| 右键菜单 | 右键（状态选择、漫游开关、退出） |

## 动画状态

| 状态 | 描述 | FPS |
|------|------|-----|
| idle | 待机呼吸 | 8 |
| running-right | 向右跑 | 10 |
| running-left | 向左跑 | 10 |
| waving | 挥手 | 8 |
| jumping | 跳跃 | 10 |
| failed | 失败 | 6 |
| waiting | 等待 | 6 |
| running | 原地跑 | 10 |
| review | 审查代码 | 8 |

## 脚本说明

| 脚本 | 用途 |
|------|------|
| `pet_launch.py` | 一键启动（自动安装 hooks + daemon + 宠物） |
| `pet_daemon.py` | 后台守护进程，接收状态指令 |
| `pet_bridge.py` | 状态桥接，手动设置宠物状态 |
| `install_hooks.py` | 安装/卸载 hooks 到 settings.json |
| `desktop_pet.py` | tkinter 桌面宠物播放器 |
| `generate_demo_atlas.py` | 生成 demo 像素风精灵图集 |
| `compose_atlas.py` | 从帧图片合成图集 |
| `validate_atlas.py` | 验证图集规格 |
| `make_contact_sheet.py` | 生成缩略图网格 |

## 精灵图集规格

| 属性 | 值 |
|------|-----|
| 网格 | 8 列 × 9 行 |
| 帧尺寸 | 192 × 208 px |
| 图集尺寸 | 1536 × 1872 px |
| 格式 | PNG 透明背景 |

## 依赖

- Python 3.10+
- Pillow (`pip install Pillow`)
- tkinter（Windows/macOS 自带）

## 许可证

MIT License
