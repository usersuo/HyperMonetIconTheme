import os
import re
import shutil
import urllib
import zipfile
import threading
import xml.etree.ElementTree as ET

from io import BytesIO
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from cairosvg import svg2png
from PIL import Image, ImageColor

# Material You Monet 配色, FG_COLOR前景色，为图标本体线条颜色；BG_COLOR背景色，为图标背景画布底色
# 通常 浅色模式下，FG_COLOR为深色，BG_COLOR为浅色；深色模式下，FG_COLOR为浅色，BG_COLOR为深色

# 深色主题 蓝色
FG_COLOR = "#d1e2fc"
BG_COLOR = "#1c232b"

# 浅色主题 蓝色
# FG_COLOR = "#011c31"
# BG_COLOR = "#e8ecf7"


# 深色主题 红色
# FG_COLOR = "#fcdbcf"
# BG_COLOR = "#2d2017"

# 浅色主题 红色
# FG_COLOR = "#331300"
# BG_COLOR = "#f5eae4"


# 深色主题 绿色
# FG_COLOR = "#c7efac"
# BG_COLOR = "#1e241a"

# 浅色主题 绿色
# FG_COLOR = "#071e02"
# BG_COLOR = "#eaeee0"


# 图标大小和缩放比例
# HyperOS图标（和背景）最大为432*432，且系统会对图标本体（前景）四周进行33.3%的裁切
# 按66.6%缩放可预留裁切空间，此时图标本体长宽为432*66.6%=288，铺满背景画布，图标过大
# 按40%缩放，最终图标本体长宽为432*40%=172，效果最佳，不至于铺满背景画布
ICON_SIZE = 432  # 图标大小432*432
ICON_SCALE = 0.4  # 图标占未裁切背景画布的40%

# 图标并行处理线程数
# 最大128
# None为默认，为CPU核心数的4倍。16核 = 64线程
MAX_WORKERS = None

# 当前工作目录
current_dir = Path.cwd()

# lawnicons的原始appfilter映射文件
# original_appfilter = current_dir / "appfilter.xml"
original_appfilter = (
    current_dir / "lawnicons-develop" / "app" / "assets" / "appfilter.xml"
)

# 处理后的icon包名映射文件
# lawnicons的appfilter使用"包名/activity"而非包名来进一步细分item，一个包名可能对应多个item
# 需要对appfilter去重，确保每个包名只出现一次
icon_mapper = current_dir / "icon_mapper.xml"

# lawnicons的原始svgs目录
# svg_dir = current_dir / "svgs"
svg_dir = current_dir / "lawnicons-develop" / "svgs"


# 图标临时输出目录
output_dir = current_dir / "output"

# icons包、mtz包、magisk包模板目录
icons_template_dir = current_dir / "icons_template"
mtz_template_dir = current_dir / "mtz_template_HyperOS"
magisk_template_dir = current_dir / "magisk_template_HyperOS"

# 工件输出命名格式
target_mtz_pattern = str(
    current_dir / "mtz_theme_Lawnicons_HyperMonetTheme_{timestamp}.mtz"
)
target_magisk_pattern = str(
    current_dir / "magisk_module_Lawnicons_HyperMonetTheme_{timestamp}.zip"
)

# 运行次数反馈
# 用于Github readme统计标签
# https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-used
# https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-succeed
api_url_used = f"https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-used.svg"
api_url_succeed = (
    f"https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-succeed.svg"
)


# 映射预处理
class MappingProcessor:
    # 提取原始Appfilter中ComponentInfo的包名
    @staticmethod
    def parse_component_info(component: str) -> str:
        match = re.match(r"ComponentInfo\{([^/]+)/.*?\}", component)
        if match:
            return match.group(1)
        return ""

    # 去重并生成icon_mapper
    @staticmethod
    def convert_icon_mapper(input_path: str, output_path: str) -> None:
        # 读取并解析原始XML
        print(
            f"  (1/4) MappingProcessor.convert_icon_mapper: 已找到 appfilter ({input_path})"
        )
        tree = ET.parse(input_path)
        root = tree.getroot()
        unique_packages: Dict[str, tuple] = {}

        # 处理每个item
        print("  (2/4) MappingProcessor.convert_icon_mapper: 正在去重 appfilter")
        for item in root.findall("item"):
            component = item.get("component", "")
            name = item.get("name", "")
            drawable = item.get("drawable", "")

            if component and drawable:
                package = MappingProcessor.parse_component_info(component)
                if package:
                    unique_packages[package] = (name, drawable)

        # 创建新的xml结构
        new_root = ET.Element("resources")

        # 添加转换后的item
        for package, (name, drawable) in sorted(unique_packages.items()):
            new_item = ET.SubElement(new_root, "item")
            new_item.set("name", name)
            new_item.set("package", package)
            new_item.set("drawable", drawable)

        # 写入文件
        print("  (3/4) MappingProcessor.convert_icon_mapper: 正在生成 icon_mapper")
        tree = ET.ElementTree(new_root)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            rough_string = ET.tostring(new_root, encoding="unicode")
            formatted_string = ""
            indent = ""
            for line in rough_string.split(">"):
                if line.strip():
                    if not line.startswith("</"):
                        formatted_string += indent + line + ">\n"
                        if not line.startswith("<resources") and not line.endswith(
                            "/>"
                        ):
                            indent = "    "
                    else:
                        indent = ""
                        formatted_string += line + ">\n"

            f.write(formatted_string)
        print(
            f"  (4/4) MappingProcessor.convert_icon_mapper: icon_mapper 映射文件已生成 ({output_path})"
        )


# 图标处理
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

    # 遍历mapper，多线程处理全部图标
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


# 封装icons包，打包mtz和magisk模块
class ThemePacker:
    # 复制图标到icons模板并打包
    @staticmethod
    def pack_icons_zip(
        output_dir: str,
        icons_template_dir: str,
        mtz_template_dir=str,
        magisk_template_dir=str,
    ):
        # 检查 drawable-xxhdpi目录
        print("  (1/6) ThemePacker.pack_icons_zip: 检查目录")
        icons_template_drawable_dir = (
            Path(icons_template_dir) / "res" / "drawable-xxhdpi"
        )

        if icons_template_drawable_dir.exists():
            shutil.rmtree(icons_template_drawable_dir)
        icons_template_drawable_dir.mkdir(parents=True)

        # 移动所有图标到 icons 模板的 drawable-xxhdpi 目录
        print("  (2/6) ThemePacker.pack_icons_zip: 从 output 移动图标到 icons_template")
        for item in Path(output_dir).iterdir():
            if item.is_dir():
                # shutil.copytree(item, icons_template_drawable_dir / item.name)
                shutil.move(item, icons_template_drawable_dir / item.name)

        # 打包 icons 模板目录
        print(
            "  (3/6) ThemePacker.pack_icons_zip: 正在使用 zipfile 封装 icons_template"
        )
        temp_icons_zip = Path(icons_template_dir) / "icons.zip"

        with zipfile.ZipFile(temp_icons_zip, "w", zipfile.ZIP_STORED) as zf:
            for root, _, files in os.walk(icons_template_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, icons_template_dir)
                    zf.write(file_path, arcname)

        # 重命名 icons.zip 为 icons, 拷贝到 mtz/magisk 模板
        # print("  (4/8) ThemePacker.pack_icons_zip: 拷贝 icons 到 mtz 和 magisk 模板")
        print("  (4/6) ThemePacker.pack_icons_zip: 合入 icons 到 magisk 模板")
        final_icons = Path(icons_template_dir) / "icons"
        os.rename(temp_icons_zip, final_icons)
        shutil.copy(final_icons, mtz_template_dir)
        shutil.copy(final_icons, magisk_template_dir)

    # 打包 magisk 模块
    @staticmethod
    def pack_magisk_module(magisk_template_dir: str, target_magisk_pattern: str):

        print(
            "  (5/6) ThemePacker.pack_magisk_module: 正在使用 zipfile 封装 magisk_template_HyperOS2"
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_magisk = target_magisk_pattern.format(timestamp=timestamp)

        with zipfile.ZipFile(target_magisk, "w", zipfile.ZIP_STORED) as zf:
            # 打包模板中的所有文件,除了 icons 目录
            for root, dirs, files in os.walk(magisk_template_dir):
                if "icons" in root:
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, magisk_template_dir)
                    zf.write(file_path, arcname)

        print(
            f"  (6/6) ThemePacker.pack_magisk_module: magisk 模块已生成({target_magisk})"
        )

    # 打包 mtz (不建议)
    @staticmethod
    def pack_mtz(mtz_template_dir: str, target_mtz_pattern: str):

        print(
            "  (7/8) ThemePacker.pack_mtz: 正在使用 zipfile 封装 mtz_template_HyperOS2"
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_mtz = target_mtz_pattern.format(timestamp=timestamp)

        with zipfile.ZipFile(target_mtz, "w", zipfile.ZIP_STORED) as zf:
            # 打包模板中的所有文件,除了 icons 目录
            for root, dirs, files in os.walk(mtz_template_dir):
                if "icons" in root:
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, mtz_template_dir)
                    zf.write(file_path, arcname)
        print(f"  (8/8) ThemePacker.pack_mtz: mtz 已生成({target_mtz})")


# 清理临时文件
class Cleaner:
    @staticmethod
    def cleanup(current_dir: str):
        clean_up = [
            current_dir / "output",
            current_dir / "icons_template" / "res" / "drawable-xxhdpi",
            current_dir / "icons_template" / "icons.zip",
            current_dir / "icons_template" / "icons",
            current_dir / "mtz_template_HyperOS" / "icons",
            current_dir / "magisk_template_HyperOS" / "icons",
            current_dir / "icon_mapper.xml",
        ]
        print(f"  (1/1) Cleaner.cleanup: 正在清理")
        for file in clean_up:
            if file.exists():
                if os.path.isfile(str(file)):
                    os.remove(str(file))
                    print(f"    已删除文件: {file}")
                else:
                    shutil.rmtree(str(file))
                    print(f"    已删除目录: {file}")


# 运行次数统计
# 用于Github readme标签
# https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-used
# https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-succeed
class UsageCounter:
    @staticmethod
    def request_hits(api_url: str):
        request = urllib.request.Request(
            api_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
            },
        )

        urllib.request.urlopen(request)


def main():
    # 运行前统计
    UsageCounter.request_hits(api_url_used)

    # 清理临时文件
    print("(1/4) Cleaner: 开始清理临时文件")
    Cleaner.cleanup(current_dir)

    # 处理映射
    print("\n(2/4) MappingProcessor: 开始处理映射")
    MappingProcessor.convert_icon_mapper(str(original_appfilter), str(icon_mapper))

    # 处理图标
    print("\n(3/4) IconProcessor: 开始处理图标")
    IconProcessor.generate_icons(
        icon_mapper_path=str(icon_mapper),
        svg_dir=str(svg_dir),
        output_dir=str(output_dir),
        fg_color=FG_COLOR,
        bg_color=BG_COLOR,
        icon_size=ICON_SIZE,
        icon_scale=ICON_SCALE,
        max_workers=MAX_WORKERS,
    )

    # 打包icons
    print("\n(4/4) ThemePacker: 开始打包")
    ThemePacker.pack_icons_zip(
        output_dir=str(output_dir),
        icons_template_dir=str(icons_template_dir),
        mtz_template_dir=str(mtz_template_dir),
        magisk_template_dir=str(magisk_template_dir),
    )

    # 打包magisk模块
    ThemePacker.pack_magisk_module(
        magisk_template_dir=str(magisk_template_dir),
        target_magisk_pattern=target_magisk_pattern,
    )

    # 打包mtz (不建议)
    # 务必优先使用magisk模块，因为mtz模板好像还有点问题
    # mtz应用打开动画和圆角可能有问题，且某些图标可能无法生效
    # 受系统版本影响较大
    # 使用mtz时桌面高级材质会丢失。magisk模块无此问题
    # 导入mtz需要主题破解

    # ThemePacker.pack_mtz(
    #     mtz_template_dir=str(mtz_template_dir),
    #     target_mtz_pattern=target_mtz_pattern
    # )

    print("\n处理完成, 工件已保存至当前目录")
    print("刷入后请重启设备")

    # 运行后统计
    UsageCounter.request_hits(api_url_succeed)


if __name__ == "__main__":
    main()
