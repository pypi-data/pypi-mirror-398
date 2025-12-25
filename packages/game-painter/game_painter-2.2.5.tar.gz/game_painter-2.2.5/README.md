# 🎨 GamePainter - 基础绘图工具

> 提供 17 个核心绘图工具，通过组合可绑制任意复杂图形！集成 AI 生图能力！

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/game-painter.svg)](https://pypi.org/project/game-painter/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 特性

- 🎨 **17 个核心工具** - 精简设计，功能完整
- 🤖 **AI 生图集成** - [Seedream4.5 AI生图](https://www.volcengine.com/docs/82379/1824121?lang=zh)
- 🔧 **MCP 工具集成** - 可被 AI 助手直接调用
- 📐 **灵活组合** - 基础图形组合成复杂图案
- 🖼️ **图片处理** - 清除背景、裁切、缩放、扩充等
- 🚀 **开箱即用** - 无需复杂配置

## 🚀 快速开始

### 安装

从 PyPI 安装（推荐）：

```bash
# 基础安装（16个核心绘图工具）
pip install game-painter
```

或从源码安装：

```bash
# 克隆项目
git clone https://github.com/dzqdzq/game-painter.git
cd game-painter

# 创建虚拟环境并安装依赖
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 基础安装
pip install -e .
```

## 🔌 MCP 工具配置

安装完成后，在 Cursor 或 Claude Desktop 中配置 MCP 服务器。

### Cursor 配置

打开 Cursor Settings，找到 MCP 设置，添加配置：

```json
{
  "mcpServers": {
    "game-painter": {
      "command": "uvx",
      "args": ["game-painter"],
      "env":{
        "ARK_DOUBAO_SEEDREAM_API_KEY": 'your api key'
      }
    }
  }
}

```

## 🛠️ 工具列表 (17 个)

### 画布管理

| 工具 | 说明 |
|------|------|
| `create_canvas` | 创建画布（第一步） |
| `save` | 保存画布为图片 |

### 线条类

| 工具 | 说明 |
|------|------|
| `line` | 直线/虚线 |
| `polyline` | 折线/多段线 |
| `arc` | 弧线 |
| `bezier` | 贝塞尔曲线 |
| `wave` | 波浪线 |

### 形状类

| 工具 | 说明 |
|------|------|
| `rect` | 矩形/圆角矩形 |
| `ellipse` | 椭圆/正圆 |
| `polygon` | 多边形（三角形、六边形等） |

### 图标类

| 工具 | 说明 |
|------|------|
| `icon` | 五角星、箭头 |

### 辅助类

| 工具 | 说明 |
|------|------|
| `text` | 文字 |

### 图片处理类

| 工具 | 说明 |
|------|------|
| `remove_background` | AI 智能清除背景 |
| `resize_image` | 缩放图片 |
| `auto_crop_transparent` | 自动裁切透明区域（PNG） |
| `crop_region` | 扩充透明区域到指定大小 |

### AI 生图类（可选）

| 工具 | 说明 |
|------|------|
| `generate_image` | 火山引擎即梦 AI 文生图（需配置 API Key） |

> ⚠️ **AI 生图功能需要：**
> 1. 配置环境变量 `ARK_DOUBAO_SEEDREAM_API_KEY`
> 2. 满足以上条件后，`generate_image` 工具才会出现在工具列表中

## 📄 License

MIT License
