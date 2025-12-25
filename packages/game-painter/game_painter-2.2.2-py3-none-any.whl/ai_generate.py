#!/usr/bin/env python3
"""
AI 图片生成模块 - 火山引擎即梦 AI
独立的 AI 生图功能，可选配置
"""

import os
import io
import base64
from typing import List, Optional
from urllib.request import urlopen
from mcp.types import Tool, TextContent, ImageContent

try:
    from volcenginesdkarkruntime import Ark
    from volcenginesdkarkruntime.types.images.images import SequentialImageGenerationOptions
    VOLCENGINE_AVAILABLE = True
except ImportError:
    VOLCENGINE_AVAILABLE = False


def is_ai_generate_enabled() -> bool:
    """
    检查 AI 生图功能是否启用
    需要同时满足：
    1. 依赖包已安装
    2. 环境变量 ARK_DOUBAO_SEEDREAM_API_KEY 已配置
    """
    if not VOLCENGINE_AVAILABLE:
        return False
    
    api_key = os.getenv('ARK_DOUBAO_SEEDREAM_API_KEY')
    return api_key is not None and api_key.strip() != ""


def get_ai_generate_tool() -> Optional[Tool]:
    """
    获取 AI 生图工具定义
    如果未启用则返回 None
    """
    if not is_ai_generate_enabled():
        return None
    
    return Tool(
        name="generate_image",
        description="使用火山引擎即梦AI模型（Doubao SeeDream）根据文字提示生成高质量图片。支持多种尺寸、连续生图、风格控制等功能。适用于创作插画、设计素材、概念图等。",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "图片生成的文字提示。描述越详细，生成效果越好。可以包括主题、风格、色彩、构图等信息。"
                },
                "model": {
                    "type": "string",
                    "description": "AI模型ID。",
                    "default": "doubao-seedream-4-5-251128",
                    "enum": ["doubao-seedream-4-5-251128"]
                },
                "size": {
                    "type": "string",
                    "description": "生成图片的尺寸。格式：宽x高，如 '1024x1024'。常用尺寸：1024x1024（正方形）、1920x1080（16:9横屏）、1080x1920（9:16竖屏）、2000x2000（高清）。",
                    "default": "1024x1024",
                    "enum": ["1024x1024", "1920x1080", "1080x1920", "2000x2000", "512x512"]
                },
                "sequential_image_generation": {
                    "type": "string",
                    "description": "连续生图模式。'auto'=自动连续生成多张，'manual'=手动控制，'off'=关闭（生成单张）。",
                    "default": "off",
                    "enum": ["auto", "manual", "off"]
                },
                "max_images": {
                    "type": "integer",
                    "description": "连续生图时最大生成图片数量（1-10）。仅在 sequential_image_generation 不为 'off' 时有效。",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 10
                },
                "watermark": {
                    "type": "boolean",
                    "description": "是否在生成的图片上添加水印。",
                    "default": False
                }
            },
            "required": ["prompt"]
        }
    )


async def handle_generate_image(arguments: dict) -> List:
    """
    处理 AI 生图请求
    
    Args:
        arguments: 工具调用参数
        
    Returns:
        包含文本和图片内容的列表
    """
    try:
        # 检查是否启用
        if not is_ai_generate_enabled():
            return [TextContent(
                type="text",
                text="❌ AI 生图功能未启用。请安装依赖并配置环境变量: ARK_DOUBAO_SEEDREAM_API_KEY"
            )]
        
        # 获取 API Key
        api_key = os.getenv('ARK_DOUBAO_SEEDREAM_API_KEY')
        
        # 获取参数
        prompt = arguments.get("prompt")
        if not prompt:
            return [TextContent(type="text", text="❌ 必须提供 prompt 参数")]
        
        model = arguments.get("model", "doubao-seedream-4-5-251128")
        size = arguments.get("size", "1024x1024")
        sequential_mode = arguments.get("sequential_image_generation", "off")
        max_images = arguments.get("max_images", 1)
        watermark = arguments.get("watermark", False)
        
        # 创建客户端
        client = Ark(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key,
        )
        
        # 准备连续生图选项
        seq_options = None
        if sequential_mode != "off":
            seq_options = SequentialImageGenerationOptions(max_images=max_images)
        
        # 调用生图 API（流式）
        stream = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            image=[],
            response_format="url",
            sequential_image_generation=sequential_mode,
            sequential_image_generation_options=seq_options,
            watermark=watermark,
            stream=True,
        )
        
        # 收集生成的图片 URL
        image_urls = []
        error_msg = None
        usage_info = None
        
        for event in stream:
            if event is None:
                continue
            
            if event.type == "image_generation.partial_failed":
                error_msg = f"生成失败: {event.error.message if event.error else '未知错误'}"
                if event.error and hasattr(event.error, 'code'):
                    if str(event.error.code) == "InternalServiceError":
                        break
            
            elif event.type == "image_generation.partial_succeeded":
                if event.error is None and event.url:
                    image_urls.append({
                        "url": event.url,
                        "size": event.size
                    })
            
            elif event.type == "image_generation.completed":
                if event.error is None and event.usage:
                    usage_info = event.usage
        
        if error_msg:
            return [TextContent(type="text", text=f"❌ {error_msg}")]
        
        if not image_urls:
            return [TextContent(type="text", text="❌ 未生成任何图片")]
        
        # 下载图片并转换为 base64
        results = []
        
        # 添加成功提示
        usage_text = f"用量: 生成了 {usage_info.generated_images} 张图片" if usage_info else ""
        results.append(TextContent(
            type="text", 
            text=f"✅ 图片生成成功\n提示词: {prompt}\n模型: {model}\n尺寸: {size}\n数量: {len(image_urls)} 张\n{usage_text}"
        ))
        
        # 下载并返回每张图片
        for idx, img_info in enumerate(image_urls, 1):
            try:
                # 从 URL 下载图片
                with urlopen(img_info["url"]) as response:
                    image_data = response.read()
                    img_base64 = base64.b64encode(image_data).decode("utf-8")
                    
                    results.append(ImageContent(
                        type="image",
                        data=img_base64,
                        mimeType="image/png"
                    ))
            except Exception as download_error:
                results.append(TextContent(
                    type="text",
                    text=f"⚠️ 图片 {idx} 下载失败: {str(download_error)}\nURL: {img_info['url']}"
                ))
        
        return results
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ AI 生成图片失败: {str(e)}")]

