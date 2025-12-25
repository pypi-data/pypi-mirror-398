"""
🎨 GamePainter - 基础绘图库
提供画布创建和基础绘图功能，通过组合可绑制任意复杂图形
"""

from PIL import Image, ImageDraw, ImageFont
import math
import os
import io
import base64
from typing import Tuple, Optional, List, Literal


class GamePainter:
    """
    🎨 基础画布绑制器
    
    提供核心绑图能力：线条、形状、图标、文字等
    """
    
    def __init__(self, width: int, height: int, bg_color: Tuple[int, ...] = (0, 0, 0, 0)):
        """
        初始化画布
        
        Args:
            width: 画布宽度（像素）
            height: 画布高度（像素）  
            bg_color: 背景颜色 RGBA，默认透明
        """
        self.width = width
        self.height = height
        self.image = Image.new("RGBA", (width, height), bg_color)
        self.draw = ImageDraw.Draw(self.image)
    
    def _ensure_rgba(self, color: Tuple[int, ...]) -> Tuple[int, int, int, int]:
        """确保颜色是 RGBA 格式"""
        if len(color) == 3:
            return (*color, 255)
        return color[:4]
    
    def _binomial(self, n: int, k: int) -> int:
        """计算二项式系数 C(n, k)"""
        if k < 0 or k > n:
            return 0
        if k == 0 or k == n:
            return 1
        result = 1
        for i in range(min(k, n - k)):
            result = result * (n - i) // (i + 1)
        return result
    
    def _bezier_point(self, points: List[Tuple[int, int]], t: float) -> Tuple[float, float]:
        """计算贝塞尔曲线上的点"""
        n = len(points) - 1
        x = 0
        y = 0
        for i, (px, py) in enumerate(points):
            coef = self._binomial(n, i) * (1 - t) ** (n - i) * t ** i
            x += coef * px
            y += coef * py
        return (x, y)
    
    def _draw_dashed_line(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        color: Tuple[int, ...],
        width: int,
        dash: List[int]
    ):
        """绘制虚线"""
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return
        
        ux = dx / length
        uy = dy / length
        
        dash_len = dash[0] if len(dash) > 0 else 10
        gap_len = dash[1] if len(dash) > 1 else 5
        
        pos = 0
        draw_segment = True
        
        while pos < length:
            if draw_segment:
                seg_len = min(dash_len, length - pos)
                sx = x1 + ux * pos
                sy = y1 + uy * pos
                ex = x1 + ux * (pos + seg_len)
                ey = y1 + uy * (pos + seg_len)
                self.draw.line([(int(sx), int(sy)), (int(ex), int(ey))], fill=color, width=width)
                pos += dash_len
            else:
                pos += gap_len
            draw_segment = not draw_segment
    
    # ==================== 线条类 ====================
    
    def pen_line(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        color: Tuple[int, ...] = (0, 0, 0, 255),
        width: int = 2,
        dash: Optional[List[int]] = None
    ):
        """
        画直线（支持虚线）
        
        Args:
            x1, y1: 起点
            x2, y2: 终点
            color: 颜色 RGBA
            width: 线宽
            dash: 虚线模式 [线段长, 间隔长]
        """
        color = self._ensure_rgba(color)
        
        if dash is None:
            self.draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
        else:
            self._draw_dashed_line(x1, y1, x2, y2, color, width, dash)
    
    def pen_lines(
        self,
        points: List[Tuple[int, int]],
        color: Tuple[int, ...] = (0, 0, 0, 255),
        width: int = 2,
        closed: bool = False,
        dash: Optional[List[int]] = None
    ):
        """
        画折线（支持虚线）
        
        Args:
            points: 点列表 [(x1,y1), (x2,y2), ...]
            color: 颜色 RGBA
            width: 线宽
            closed: 是否闭合
            dash: 虚线模式 [线段长, 间隔长]
        """
        if len(points) < 2:
            return
        
        color = self._ensure_rgba(color)
        
        if closed:
            points = list(points) + [points[0]]
        
        if dash is None:
            self.draw.line(points, fill=color, width=width, joint="curve")
        else:
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                self._draw_dashed_line(x1, y1, x2, y2, color, width, dash)
    
    def pen_arc(
        self,
        x: int, y: int,
        width: int, height: int,
        start_angle: float = 0,
        end_angle: float = 180,
        color: Tuple[int, ...] = (0, 0, 0, 255),
        line_width: int = 2
    ):
        """
        画弧线
        
        Args:
            x, y: 外接矩形左上角
            width, height: 外接矩形尺寸
            start_angle: 起始角度（度）
            end_angle: 结束角度（度）
            color: 颜色 RGBA
            line_width: 线宽
        """
        color = self._ensure_rgba(color)
        self.draw.arc([x, y, x + width - 1, y + height - 1], 
                     start=start_angle, end=end_angle, fill=color, width=line_width)
    
    def pen_bezier(
        self,
        points: List[Tuple[int, int]],
        color: Tuple[int, ...] = (0, 0, 0, 255),
        width: int = 2,
        steps: int = 50
    ):
        """
        画贝塞尔曲线
        
        Args:
            points: 控制点列表（2=直线, 3=二次, 4=三次）
            color: 颜色 RGBA
            width: 线宽
            steps: 采样步数
        """
        if len(points) < 2:
            return
        
        color = self._ensure_rgba(color)
        
        curve_points = []
        for i in range(steps + 1):
            t = i / steps
            point = self._bezier_point(points, t)
            curve_points.append((int(point[0]), int(point[1])))
        
        if len(curve_points) >= 2:
            self.draw.line(curve_points, fill=color, width=width, joint="curve")
    
    def pen_wave(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        color: Tuple[int, ...] = (0, 0, 0, 255),
        width: int = 2,
        amplitude: int = 10,
        wavelength: int = 20
    ):
        """
        画波浪线
        
        Args:
            x1, y1: 起点
            x2, y2: 终点
            color: 颜色 RGBA
            width: 线宽
            amplitude: 波浪振幅
            wavelength: 波长
        """
        color = self._ensure_rgba(color)
        
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return
        
        ux = dx / length
        uy = dy / length
        px = -uy
        py = ux
        
        points = []
        steps = int(length / 2)
        
        for i in range(steps + 1):
            t = i / steps * length
            wave_offset = amplitude * math.sin(2 * math.pi * t / wavelength)
            cx = x1 + ux * t + px * wave_offset
            cy = y1 + uy * t + py * wave_offset
            points.append((int(cx), int(cy)))
        
        if len(points) >= 2:
            self.draw.line(points, fill=color, width=width, joint="curve")
    
    # ==================== 形状类 ====================
    
    def pen_rect(
        self,
        x: int, y: int,
        width: int, height: int,
        fill_color: Optional[Tuple[int, ...]] = None,
        border_color: Optional[Tuple[int, ...]] = (0, 0, 0, 255),
        border_width: int = 2,
        radius: int = 0
    ):
        """
        画矩形（支持圆角）
        
        Args:
            x, y: 左上角
            width, height: 尺寸
            fill_color: 填充颜色 RGBA
            border_color: 边框颜色 RGBA
            border_width: 边框宽度
            radius: 圆角半径（0为直角）
        """
        if fill_color:
            fill_color = self._ensure_rgba(fill_color)
        if border_color:
            border_color = self._ensure_rgba(border_color)
        
        if radius > 0:
            self.draw.rounded_rectangle(
                [x, y, x + width - 1, y + height - 1],
                radius=radius,
                fill=fill_color,
                outline=border_color,
                width=border_width
            )
        else:
            self.draw.rectangle(
                [x, y, x + width - 1, y + height - 1],
                fill=fill_color,
                outline=border_color,
                width=border_width
            )
    
    def pen_ellipse(
        self,
        x: int, y: int,
        width: int, height: int,
        fill_color: Optional[Tuple[int, ...]] = None,
        border_color: Optional[Tuple[int, ...]] = (0, 0, 0, 255),
        border_width: int = 2
    ):
        """
        画椭圆/圆形
        
        Args:
            x, y: 外接矩形左上角
            width, height: 尺寸（相等则为正圆）
            fill_color: 填充颜色 RGBA
            border_color: 边框颜色 RGBA
            border_width: 边框宽度
        """
        if fill_color:
            fill_color = self._ensure_rgba(fill_color)
        if border_color:
            border_color = self._ensure_rgba(border_color)
        
        self.draw.ellipse([x, y, x + width - 1, y + height - 1], 
                         fill=fill_color, outline=border_color, width=border_width)
    
    def pen_polygon(
        self,
        points: List[Tuple[int, int]],
        fill_color: Optional[Tuple[int, ...]] = None,
        border_color: Optional[Tuple[int, ...]] = (0, 0, 0, 255),
        border_width: int = 2
    ):
        """
        画多边形（自定义顶点）
        
        Args:
            points: 顶点列表 [(x1,y1), (x2,y2), ...]
            fill_color: 填充颜色 RGBA
            border_color: 边框颜色 RGBA
            border_width: 边框宽度
        """
        if fill_color:
            fill_color = self._ensure_rgba(fill_color)
        if border_color:
            border_color = self._ensure_rgba(border_color)
        
        self.draw.polygon(points, fill=fill_color, outline=border_color, width=border_width)
    
    def pen_regular_polygon(
        self,
        cx: int, cy: int,
        radius: int,
        sides: int = 6,
        rotation: float = 0,
        fill_color: Optional[Tuple[int, ...]] = None,
        border_color: Optional[Tuple[int, ...]] = (0, 0, 0, 255),
        border_width: int = 2
    ):
        """
        画正多边形
        
        Args:
            cx, cy: 中心坐标
            radius: 外接圆半径
            sides: 边数（3=三角形, 4=正方形, 6=六边形）
            rotation: 旋转角度（度），0度时第一个顶点朝上
            fill_color: 填充颜色 RGBA
            border_color: 边框颜色 RGBA
            border_width: 边框宽度
        """
        if fill_color:
            fill_color = self._ensure_rgba(fill_color)
        if border_color:
            border_color = self._ensure_rgba(border_color)
        
        rot_rad = math.radians(rotation - 90)
        
        points = []
        for i in range(sides):
            angle = rot_rad + (2 * math.pi * i / sides)
            px = cx + radius * math.cos(angle)
            py = cy + radius * math.sin(angle)
            points.append((int(px), int(py)))
        
        self.draw.polygon(points, fill=fill_color, outline=border_color, width=border_width)
    
    # ==================== 图标类 ====================
    
    def pen_star(
        self,
        cx: int, cy: int,
        outer_radius: int,
        inner_radius: Optional[int] = None,
        points: int = 5,
        rotation: float = 0,
        fill_color: Optional[Tuple[int, ...]] = (255, 215, 0, 255),
        border_color: Optional[Tuple[int, ...]] = (218, 165, 32, 255),
        border_width: int = 2
    ):
        """
        画星形
        
        Args:
            cx, cy: 中心坐标
            outer_radius: 外圈半径（角尖）
            inner_radius: 内圈半径（凹陷），默认为外圈的0.4倍
            points: 星角数量
            rotation: 旋转角度（度）
            fill_color: 填充颜色 RGBA
            border_color: 边框颜色 RGBA
            border_width: 边框宽度
        """
        if fill_color:
            fill_color = self._ensure_rgba(fill_color)
        if border_color:
            border_color = self._ensure_rgba(border_color)
        
        if inner_radius is None:
            inner_radius = int(outer_radius * 0.4)
        
        rot_rad = math.radians(rotation - 90)
        
        vertices = []
        for i in range(points * 2):
            angle = rot_rad + math.pi * i / points
            r = outer_radius if i % 2 == 0 else inner_radius
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            vertices.append((int(px), int(py)))
        
        self.draw.polygon(vertices, fill=fill_color, outline=border_color, width=border_width)
    
    def pen_arrow_shape(
        self,
        cx: int, cy: int,
        size: int,
        direction: Literal["up", "down", "left", "right"] = "right",
        fill_color: Tuple[int, ...] = (255, 165, 0, 255),
        border_color: Optional[Tuple[int, ...]] = None,
        border_width: int = 2
    ):
        """
        画箭头形状
        
        Args:
            cx, cy: 中心坐标
            size: 箭头大小
            direction: 方向 up/down/left/right
            fill_color: 填充颜色 RGBA
            border_color: 边框颜色 RGBA
            border_width: 边框宽度
        """
        fill_color = self._ensure_rgba(fill_color)
        if border_color:
            border_color = self._ensure_rgba(border_color)
        
        half = size // 2
        quarter = size // 4
        
        if direction == "right":
            points = [
                (cx - half, cy - quarter),
                (cx, cy - quarter),
                (cx, cy - half),
                (cx + half, cy),
                (cx, cy + half),
                (cx, cy + quarter),
                (cx - half, cy + quarter),
            ]
        elif direction == "left":
            points = [
                (cx + half, cy - quarter),
                (cx, cy - quarter),
                (cx, cy - half),
                (cx - half, cy),
                (cx, cy + half),
                (cx, cy + quarter),
                (cx + half, cy + quarter),
            ]
        elif direction == "up":
            points = [
                (cx - quarter, cy + half),
                (cx - quarter, cy),
                (cx - half, cy),
                (cx, cy - half),
                (cx + half, cy),
                (cx + quarter, cy),
                (cx + quarter, cy + half),
            ]
        else:  # down
            points = [
                (cx - quarter, cy - half),
                (cx - quarter, cy),
                (cx - half, cy),
                (cx, cy + half),
                (cx + half, cy),
                (cx + quarter, cy),
                (cx + quarter, cy - half),
            ]
        
        self.draw.polygon(points, fill=fill_color, outline=border_color, width=border_width)
    
    # ==================== 辅助类 ====================
    
    def pen_point(
        self,
        x: int, y: int,
        color: Tuple[int, ...] = (0, 0, 0, 255),
        size: int = 3
    ):
        """
        画点
        
        Args:
            x, y: 位置
            color: 颜色 RGBA
            size: 点大小
        """
        color = self._ensure_rgba(color)
        r = size // 2
        self.draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
    
    def pen_text(
        self,
        x: int, y: int,
        text: str,
        color: Tuple[int, ...] = (0, 0, 0, 255),
        font_size: int = 16,
        font_path: Optional[str] = None
    ):
        """
        写文字
        
        Args:
            x, y: 位置
            text: 文字内容
            color: 颜色 RGBA
            font_size: 字体大小
            font_path: 字体路径
        """
        color = self._ensure_rgba(color)
        
        try:
            if font_path:
                font = ImageFont.truetype(font_path, font_size)
            else:
                # 尝试多个系统字体路径
                font_paths = [
                    "/System/Library/Fonts/PingFang.ttc",  # macOS
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                    "C:/Windows/Fonts/msyh.ttc",  # Windows
                ]
                font = None
                for path in font_paths:
                    if os.path.exists(path):
                        font = ImageFont.truetype(path, font_size)
                        break
                if font is None:
                    font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
        
        self.draw.text((x, y), text, fill=color, font=font)
    
    # ==================== 输出方法 ====================
    
    def save(self, file_path: str) -> str:
        """
        保存图片到文件
        
        Args:
            file_path: 保存路径
            
        Returns:
            保存的文件绝对路径
        """
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        self.image.save(file_path)
        return os.path.abspath(file_path)
    
    def to_bytes(self, format: str = "PNG") -> bytes:
        """将图片转换为字节数据"""
        buffer = io.BytesIO()
        self.image.save(buffer, format=format)
        return buffer.getvalue()
    
    def to_base64(self, format: str = "PNG") -> str:
        """将图片转换为 Base64 字符串"""
        return base64.b64encode(self.to_bytes(format)).decode("utf-8")
