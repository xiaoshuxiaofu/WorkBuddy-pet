---
name: workbuddy-pet
description: WorkBuddy 桌面宠物生成与播放器。当用户想要创建、自定义或启动桌面宠物伙伴时使用。触发词包括"/pet""孵化宠物""启动桌面宠物""创建宠物""看看宠物"等。支持聊天感知模式，通过 hooks 自动同步 agent 状态。
agent_created: true
---

# WorkBuddy Pet

## /pet 命令

当用户输入 `/pet` 时，**立即执行以下命令启动宠物**（无需询问）：

```bash
python ~/.workbuddy/skills/workbuddy-pet/scripts/pet_launch.py
```

如果宠物已经在运行，先检查 daemon 状态再决定。

## 概述

生成 Codex 兼容的精灵图集宠物，以 tkinter 透明窗口的形式显示在桌面。支持 9 种动画状态、拖拽移动、右键菜单、双击切换状态、自动漫游，以及**聊天感知模式**——宠物会实时反映 AI agent 的当前工作状态，配合像素风对话气泡和完成提示音。

## 快速开始

### 方式一：首次启动（自动安装 hooks）

```bash
python <SKILL_DIR>/scripts/pet_launch.py
```

首次运行会自动将 hooks 注入到 `~/.workbuddy/settings.json`，后续重启 WorkBuddy 即可通过 hooks 自动触发。

### 方式二：手动安装 hooks

```bash
# 安装 hooks 到 settings.json（幂等，重复运行不会重复添加）
python <SKILL_DIR>/scripts/install_hooks.py

# 卸载 hooks
python <SKILL_DIR>/scripts/install_hooks.py --uninstall
```

安装后重启 WorkBuddy，hooks 生效。

> **注意**：`desktop_pet.py` 必须传入 `--atlas` 参数才能运行，不要直接运行它。**始终使用 `pet_launch.py` 来启动或重启宠物。**

### 方式三：手动启动（调试用）

```bash
# Step 1: 启动 daemon
python <SKILL_DIR>/scripts/pet_daemon.py &

# Step 2: 启动宠物（必须带 --atlas）
python <SKILL_DIR>/scripts/desktop_pet.py --atlas <SKILL_DIR>/assets/demo/blue-slime_atlas.png --manifest <SKILL_DIR>/assets/demo/pet.json --scale 2.0
```

### 重启宠物

```bash
# 杀掉所有 python 进程后重新启动
taskkill /F /IM python.exe
python <SKILL_DIR>/scripts/pet_launch.py
```

## Hooks 说明

宠物通过 WorkBuddy hooks 实现状态同步。hooks 需要注册在 `~/.workbuddy/settings.json` 的 `hooks` 字段中：

| 事件 | 宠物状态 | 气泡文字 |
|------|---------|---------|
| `UserPromptSubmit` | thinking | "正在思考..." |
| `PreToolUse` | thinking | "正在思考..." |
| `PostToolUse` | running | "工作中..." |
| `Stop` | waving | "完成！" + 提示音 |
| `SessionEnd` | idle | — |

## 聊天感知模式

宠物通过轮询 `~/.workbuddy/pet_state.json`（每 500ms）读取状态：

- **Hooks 驱动**：hooks 调用 `pet_bridge.py` 更新状态 → daemon 写入 state 文件 → 宠物读取并切换动画
- **手动控制**：`python <SKILL_DIR>/scripts/pet_bridge.py <状态> [消息]` 可随时手动设置
- **状态持久**：各状态不会自动恢复，由下一个 hook 事件驱动切换
- **OK 按钮**：完成时宠物下方出现 OK 按钮，点击可聚焦 WorkBuddy 窗口并回到待机
- **提示音**：仅在进入 waving（完成）状态时播放系统提示音
- **声音开关**：右键菜单可切换提示音开关，设置持久化到 `~/.workbuddy/pet_config.json`

### 手动 bridge 用法
```bash
python <SKILL_DIR>/scripts/pet_bridge.py thinking "正在思考..."
python <SKILL_DIR>/scripts/pet_bridge.py running "工作中..."
python <SKILL_DIR>/scripts/pet_bridge.py waving "完成！"
python <SKILL_DIR>/scripts/pet_bridge.py idle
```

可用状态：`idle`, `thinking`, `running`, `coding`, `writing`, `reading`, `review`, `waving`, `failed`

## 核心功能

### 1. 启动桌面宠物

使用精灵图集启动宠物窗口，出现在屏幕右下角。

**参数：**
- `--atlas`（必填）：精灵图集 PNG 路径
- `--manifest`（可选）：pet.json 清单文件路径
- `--scale`（可选）：缩放倍数，默认 2.0

**操作：**
| 操作 | 方式 |
|------|------|
| 拖拽宠物 | 左键拖拽 |
| 切换状态 | 双击（循环切换） |
| 右键菜单 | 右键（状态选择、漫游开关、退出） |

### 2. 生成精灵图集

支持内置预设和自定义颜色：

```bash
# 默认蓝色史莱姆
python <SKILL_DIR>/scripts/generate_demo_atlas.py --output <输出目录>

# 内置预设
python <SKILL_DIR>/scripts/generate_demo_atlas.py --output <dir> --preset kunkun --name kunkun
python <SKILL_DIR>/scripts/generate_demo_atlas.py --output <dir> --preset milk-frog --name milk-frog

# 自定义颜色
python <SKILL_DIR>/scripts/generate_demo_atlas.py --output <dir> --name mypet --type frog --body 230,160,50 --eye 40,60,40

# 可用预设: blue-slime, kunkun (暗色青系史莱姆), milk-frog (橙色青蛙)
# 可用类型: slime, frog
```

### 3. 从帧图片合成图集

```bash
python <SKILL_DIR>/scripts/compose_atlas.py --input-dir <帧目录> --output <图集.png> --name <宠物名>
```

目录结构：
```
frames_dir/
    idle/           frame_0.png ... frame_7.png
    running-right/  frame_0.png ... frame_7.png
    running-left/   frame_0.png ... frame_7.png
    waving/         frame_0.png ... frame_7.png
    jumping/        frame_0.png ... frame_7.png
    failed/         frame_0.png ... frame_7.png
    waiting/        frame_0.png ... frame_7.png
    running/        frame_0.png ... frame_7.png
    review/         frame_0.png ... frame_7.png
```

### 4. 验证图集

```bash
python <SKILL_DIR>/scripts/validate_atlas.py --atlas <图集.png> --manifest <pet.json>
```

### 5. 生成缩略图

```bash
python <SKILL_DIR>/scripts/make_contact_sheet.py --atlas <图集.png> --output <缩略图.png>
```

## 精灵图集规格

| 属性 | 值 |
|------|-----|
| 网格 | 8 列 x 9 行 |
| 帧尺寸 | 192 x 208 px |
| 图集尺寸 | 1536 x 1872 px |
| 格式 | PNG 透明背景 |

### 动画状态

| 行 | 状态 | 描述 | FPS |
|----|------|------|-----|
| 0 | idle | 待机呼吸 | 8 |
| 1 | running-right | 向右跑 | 10 |
| 2 | running-left | 向左跑 | 10 |
| 3 | waving | 挥手 | 8 |
| 4 | jumping | 跳跃 | 10 |
| 5 | failed | 失败 | 6 |
| 6 | waiting | 等待 | 6 |
| 7 | running | 原地跑 | 10 |
| 8 | review | 审查代码 | 8 |

## 依赖

- Python 3.10+
- Pillow (`pip install Pillow`)
- tkinter（Windows/macOS 自带）
