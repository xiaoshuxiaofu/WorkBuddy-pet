# WorkBuddy Pet — 桌面宠物

Codex 兼容的动画桌面宠物，支持聊天感知模式，随 WorkBuddy AI 状态实时切换动画。

## 当前宠物

| 宠物 | 预览 |
|------|------|
| Diana | `assets/diana/` |
| Miss Minute | `assets/miss-minute/` |
| Frieren | `assets/frieren/` |
| Homelander | `assets/homelander/` |

## 快速开始

```bash
# 一键启动
python scripts/pet_launch.py

# 或通过 WorkBuddy 输入 /pet
```

> `desktop_pet.py` 需要 `--atlas` 参数，日常使用请用 `pet_launch.py`。

### 重启
```bash
taskkill /F /IM python.exe
python scripts/pet_launch.py
```

## 功能

### 右键菜单
| 功能 | 说明 |
|------|------|
| 切换状态 | 9 种动画状态手动切换 |
| 切换宠物 | 4 个角色一键切换，记住选择 |
| 随机漫游 | 勾选后宠物自动在桌面闲逛 |
| 聊天感知模式 | 开启后随 WorkBuddy 状态联动 |
| 提示音 | 完成和请求同意时播放系统音 |

### 聊天感知联动

宠物通过 hooks 实时同步 WorkBuddy 工作状态：

| 事件 | 状态 | 气泡 |
|------|------|------|
| UserPromptSubmit | thinking | "正在思考..." |
| PreToolUse | thinking | "正在思考..." |
| PostToolUse | running | "工作中..." |
| Stop | waving | "完成！" + 提示音 |
| SessionEnd | idle | — |

### 拖拽动画
- 向左拖 → 向左跑
- 向右拖 → 向右跑
- 松手 → 恢复待机

### 请求同意
手动触发 agree 状态，宠物显示「需要确认操作」气泡和「同意」按钮，点击聚焦 WorkBuddy 窗口。

## 从 GIF 生成宠物

每个状态一个 GIF 即可合成精灵图集：

```bash
python scripts/compose_gif_atlas.py \
  --gifs-dir <GIF目录> --output <输出目录> --name <宠物名>
```

GIF 命名：`<宠物名>-<状态>.gif`

## 脚本

| 脚本 | 用途 |
|------|------|
| `pet_launch.py` | 一键启动器（daemon + 宠物窗口） |
| `desktop_pet.py` | 桌面宠物主程序（tkinter 透明窗口） |
| `pet_daemon.py` | 状态管理 HTTP 服务（端口 19876） |
| `pet_bridge.py` | CLI 桥接，手动控制状态 |
| `install_hooks.py` | 安装/卸载 WorkBuddy hooks |
| `compose_gif_atlas.py` | GIF 合成精灵图集 |
| `generate_demo_atlas.py` | 程序化生成精灵图集 |
| `compose_atlas.py` | 单帧图片合成图集 |
| `validate_atlas.py` | 验证图集规范性 |
| `make_contact_sheet.py` | 生成缩略图预览 |

## 精灵图集规格

| 属性 | 值 |
|------|-----|
| 网格 | 8 列 × 9 行 |
| 帧尺寸 | 192 × 208 px |
| 图集尺寸 | 1536 × 1872 px |
| 格式 | PNG 透明背景 |
| 逐帧时长 | manifest 支持 durations 数组（毫秒） |

## 依赖

- Python 3.10+
- Pillow (`pip install Pillow`)
- tkinter（Windows/macOS 自带）
