import os
import threading
import xml.etree.ElementTree as ET

from io import BytesIO
from pathlib import Path
from typing import Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image, ImageColor
from cairosvg import svg2png


# 图标处理器
class OutlineIconProcessor:
    """基础图标处理器

    用于生成Outlined风格图标：
    1. 背景生成
    2. SVG转换为PNG
    3. 前景色替换
    4. 尺寸缩放
    5. 图标映射解析
    6. 多线程支持
    """

    # 线程锁和计数器
    counter_lock = threading.Lock()
    processed_count = 0

    @classmethod
    def increment_counter(cls) -> int:
        """增加处理计数

        Returns:
            int: 当前处理数量
        """
        with cls.counter_lock:
            cls.processed_count += 1
            return cls.processed_count

    @classmethod
    def update_progress(
        cls, count: int, total: int, drawable_name: str, package_name: str
    ):
        """处理进度显示

        Args:
            count: 当前处理数量
            total: 总图标数量
            drawable_name: 图标名称
            package_name: 包名
        """
        with cls.counter_lock:
            percentage = (count / total) * 100
            print(
                f"\r    ({count}/{total}) {percentage:.1f}% - 正在处理: {drawable_name} ({package_name})"
                + " " * 30,
                end="",
                flush=True,
            )

    @staticmethod
    def create_background(icon_size: int, color: str) -> Image.Image:
        """创建纯色背景图层

        Args:
            icon_size: 图标尺寸
            color: 背景颜色

        Returns:
            Image.Image: 创建的背景图层
        """
        return Image.new("RGBA", (icon_size, icon_size), color)

    @classmethod
    def process_svg(
        cls, svg_path: str, fg_color: str, icon_size: int, icon_scale: float
    ) -> Image.Image:
        """处理单个SVG文件

        Args:
            svg_path: SVG文件路径
            fg_color: 前景色（线条颜色）
            icon_size: 目标尺寸
            icon_scale: 缩放比例

        Returns:
            Image.Image: 处理后的PNG图像
        """

        # 缩放后实际大小
        icon_actual_size = int(icon_size * icon_scale)

        # svg转换为png
        try:
            png_data = svg2png(
                file_obj=open(svg_path, "rb"),
                output_width=icon_actual_size,
                output_height=icon_actual_size,
            )
        except Exception as e:
            print(f"Error processing SVG {svg_path}: {e}")
            return None

        # 创建图标图像
        icon = Image.open(BytesIO(png_data))

        # 创建透明画布
        final_icon = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))

        # 居中放置图标
        paste_x = (icon_size - icon_actual_size) // 2
        paste_y = (icon_size - icon_actual_size) // 2
        final_icon.paste(icon, (paste_x, paste_y), icon)

        # 着色前景色
        if fg_color.upper() != "#000000":
            data = final_icon.getdata()
            new_data = []
            fg_color_rgb = ImageColor.getrgb(fg_color)

            for item in data:
                # 保持透明度，仅改变颜色
                if item[3] != 0:  # 如果不完全透明
                    new_data.append((*fg_color_rgb, item[3]))
                else:
                    new_data.append(item)

            final_icon.putdata(new_data)

        return final_icon

    # 解析icon_mapper映射
    @classmethod
    def parse_icon_mapper(cls, xml_path: str) -> Dict[str, str]:
        """解析图标映射文件

        Args:
            xml_path: 映射文件路径

        Returns:
            Dict[str, str]: {包名: 图标名} 的映射字典
        """
        print(f"  (1/4) OutlineIconProcessor.parse_icon_mapper: 找到并解析 icon_mapper")
        tree = ET.parse(xml_path)
        root = tree.getroot()
        return {
            item.get("package"): item.get("drawable")
            for item in root.findall("item")
            if item.get("package") and item.get("drawable")
        }

    @classmethod
    def process_single_icon(
        cls,
        package_name: str,
        drawable_name: str,
        svg_dir: Path,
        output_dir: Path,
        background: Image.Image,
        fg_color: str,
        icon_size: int,
        icon_scale: float,
        total_icons: int,
    ) -> bool:
        """处理单个图标

        Args:
            package_name: 应用包名
            drawable_name: 图标资源名
            svg_dir: SVG目录
            output_dir: 输出目录
            background: 背景图层
            fg_color: 前景色
            icon_size: 图标尺寸
            icon_scale: 图标缩放比例
            total_icons: 总图标数

        Returns:
            bool: 处理成功返回True
        """
        svg_path = svg_dir / f"{drawable_name}.svg"

        if not svg_path.exists():
            print(
                f"    (err) OutlineIconProcessor.generate_icons: 未找到对应svg文件 {drawable_name} ({package_name})"
            )
            return False

        icon_dir = output_dir / package_name
        icon_dir.mkdir(exist_ok=True)

        # 背景 0.png
        background.save(icon_dir / "0.png", "PNG")

        # 图标 1.png
        icon = cls.process_svg(str(svg_path), fg_color, icon_size, icon_scale)
        if icon:
            icon.save(icon_dir / "1.png", "PNG")
            count = cls.increment_counter()
            cls.update_progress(count, total_icons, drawable_name, package_name)
            return True
        else:
            print(
                f"    (err) OutlineIconProcessor.generate_icons: 失败 {drawable_name} ({package_name})"
            )
            return False

    @classmethod
    def generate_icons(
        cls,
        icon_mapper_path: str,
        svg_dir: str,
        output_dir: str,
        fg_color: str,
        bg_color: str,
        icon_size: int,
        icon_scale: float,
        max_workers: int,
    ) -> None:
        """批量生成轮廓风格图标

        Args:
            icon_mapper_path: 图标映射文件路径
            svg_dir: SVG源文件目录
            output_dir: 输出目录
            fg_color: 前景色
            bg_color: 背景色
            icon_size: 图标尺寸
            icon_scale: 图标缩放比例
            max_workers: 最大工作线程数
        """
        cls.processed_count = 0

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        svg_dir_path = Path(svg_dir)

        # 解析icon_mapper
        mapper = cls.parse_icon_mapper(icon_mapper_path)

        # 创建背景
        print(f"  (2/4) OutlineIconProcessor.generate_icons: 创建 {bg_color} 背景")
        background = cls.create_background(icon_size, bg_color)

        # # 设置线程数
        # if max_workers is None:
        #     max_workers = min(128, (os.cpu_count() or 1) * 4)

        total_icons = len(mapper)
        print(
            f"  (3/4) OutlineIconProcessor.generate_icons: 找到 {total_icons} 个图标需要处理，当前并行线程数 {max_workers} ，大约需要 5 分钟"
        )

        # 多线程处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_package = {
                executor.submit(
                    cls.process_single_icon,
                    package_name,
                    drawable_name,
                    svg_dir_path,
                    output_path,
                    background,
                    fg_color,
                    icon_size,
                    icon_scale,
                    total_icons,
                ): package_name
                for package_name, drawable_name in mapper.items()
            }

            successful = 0
            for future in as_completed(future_to_package):
                package_name = future_to_package[future]
                try:
                    if future.result():
                        successful += 1
                except Exception as e:
                    print(
                        f"    (err) OutlineIconProcessor.generate_icons: 处理 {package_name} 时发生错误: {e}"
                    )

        print(
            f"\n  (4/4) OutlineIconProcessor.generate_icons: 图标处理完成，成功处理 {successful}/{total_icons}"
        )
