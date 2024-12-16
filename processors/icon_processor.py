import os
import threading
import xml.etree.ElementTree as ET

from io import BytesIO
from pathlib import Path
from typing import Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image, ImageColor
from cairosvg import svg2png


# 图标处理器
class IconProcessor:
    # 线程锁
    counter_lock = threading.Lock()

    # 处理计数
    processed_count = 0

    @classmethod
    def increment_counter(cls) -> int:
        with cls.counter_lock:
            cls.processed_count += 1
            return cls.processed_count

    # 处理进度
    @classmethod
    def update_progress(
        cls, count: int, total: int, drawable_name: str, package_name: str
    ):
        with cls.counter_lock:
            percentage = (count / total) * 100
            print(
                f"\r    ({count}/{total}) {percentage:.1f}% - 正在处理: {drawable_name} ({package_name})"
                + " " * 30,
                end="",
                flush=True,
            )

    # 创建bg_color的纯色背景 0.png
    def create_background(icon_size: int, color: str) -> Image.Image:
        return Image.new("RGBA", (icon_size, icon_size), color)

    # svg2png，着色fg_color
    def process_svg(
        svg_path: str, fg_color: str, icon_size: int, icon_scale: float
    ) -> Image.Image:

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
    @staticmethod
    def parse_icon_mapper(xml_path: str) -> Dict[str, str]:
        print(f"  (1/4) IconProcessor.parse_icon_mapper: 找到并解析 icon_mapper")
        tree = ET.parse(xml_path)
        root = tree.getroot()
        return {
            item.get("package"): item.get("drawable")
            for item in root.findall("item")
            if item.get("package") and item.get("drawable")
        }

    # 处理单个图标
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

        svg_path = svg_dir / f"{drawable_name}.svg"

        if not svg_path.exists():
            print(
                f"    (err) IconProcessor.generate_icons: 未找到对应svg文件 {drawable_name} ({package_name})"
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
                f"    (err) IconProcessor.generate_icons: 失败 {drawable_name} ({package_name})"
            )
            return False

    # 处理全部图标
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
        max_workers: int = None,
    ) -> None:

        cls.processed_count = 0

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        svg_dir_path = Path(svg_dir)

        # 解析icon_mapper
        mapper = cls.parse_icon_mapper(icon_mapper_path)

        # 背景仅创建一次，所有图标共用
        print(f"  (2/4) IconProcessor.generate_icons: 创建 {bg_color} 背景")
        background = cls.create_background(icon_size, bg_color)

        # 线程数
        if max_workers is None:
            max_workers = min(128, (os.cpu_count() or 1) * 4)

        # 图标总数
        total_icons = len(mapper)
        print(
            f"  (3/4) IconProcessor.generate_icons: 找到 {total_icons} 个图标需要处理，当前并行线程数 {max_workers} ，大约需要 5 分钟"
        )

        # 多线程处理图标
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
                        f"    (err) IconProcessor.generate_icons: 处理 {package_name} 时发生错误: {e}"
                    )

        print(
            f"\n  (4/4) IconProcessor.generate_icons: 图标处理完成，成功处理 {successful}/{total_icons}"
        )
