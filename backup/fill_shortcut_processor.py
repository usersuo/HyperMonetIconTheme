from PIL import Image, ImageColor, ImageFilter, ImageDraw
from pathlib import Path
import shutil

from processors.outline_icon_processor import IconProcessor


# 填充样式快捷方式处理器
class FillShortcutProcessor:
    @staticmethod
    def process_lock_shortcut(
        svg_dir: str,
        icons_template_dir: str,
        fg_color: str,
        bg_color: str,
        fill_color: str,
        icon_size: int,
        icon_scale: float,
        supersampling_scale: float,
    ) -> None:
        print("  (1/1) 处理填充样式一键锁屏快捷方式")

        # 连续曲率圆角背景蒙版
        template_mod_icons = Path("templates/miui_mod_icons")
        drawable_dir = Path(icons_template_dir) / "res/drawable-xxhdpi"
        svg_path = Path(svg_dir) / "volumelockr.svg"

        drawable_dir.mkdir(parents=True, exist_ok=True)

        if not svg_path.exists():
            print("    (err) 未找到锁屏图标SVG文件")
            return

        # 创建背景
        background = Image.new("RGBA", (icon_size, icon_size), bg_color)

        # 超采样尺寸
        ss_size = int(icon_size * supersampling_scale)
        ss_scale = icon_scale

        # 获取超采样线条图标
        line_icon = IconProcessor.process_svg(str(svg_path), fg_color, ss_size, ss_scale)
        if not line_icon:
            print("    (err) 处理锁屏图标失败")
            return

        # 创建超采样填充层
        fill_layer = Image.new("RGBA", line_icon.size, (0, 0, 0, 0))
        fill_color_rgba = ImageColor.getrgb(fill_color)

        # 图像处理
        smoothed = line_icon.filter(ImageFilter.GaussianBlur(0.8))
        binary_mask = smoothed.convert("L").point(lambda x: 255 if x > 20 else 0)

        # 填充点选择
        width, height = binary_mask.size
        start_points = [
            (0, 0), (width-1, 0), (0, height-1), (width-1, height-1),  # 四角
            (width//2, 0), (width//2, height-1), (0, height//2), (width-1, height//2),  # 边中点
        ]

        # 填充处理
        fill_mask = binary_mask.filter(ImageFilter.SMOOTH_MORE).point(
            lambda x: 255 if x > 128 else 0
        )
        for x, y in start_points:
            ImageDraw.floodfill(fill_mask, (x, y), 128)

        # 创建填充图层 - 修改填充逻辑
        fill_pixels = fill_layer.load()
        mask_pixels = fill_mask.load()
        for y in range(height):
            for x in range(width):
                # 填充非外部区域（非128的区域）
                if mask_pixels[x, y] != 128:
                    fill_pixels[x, y] = fill_color_rgba

        # 合并图层
        final_icon = Image.alpha_composite(fill_layer, line_icon)

        # 缩小到目标尺寸
        final_icon = final_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

        # 应用圆角蒙版
        mask_path = template_mod_icons / "icon_folder.png"
        if not mask_path.exists():
            print(f"    (err) 未找到蒙版文件: {mask_path}")
            return

        mask = Image.open(mask_path).convert("L")
        mask = mask.resize((icon_size, icon_size))

        # 应用蒙版到背景
        background_copy = background.copy()
        background_copy.putalpha(mask)

        # 合并最终图层
        final_image = Image.alpha_composite(background_copy, final_icon)

        # 保存图标
        output_path = drawable_dir / "status_bar_toggle_lock.png"
        final_image.save(output_path, "PNG")
        print(f"    (1/1) 处理完成: {output_path}")

        # 复制其他图标
        for file in template_mod_icons.glob("*.png"):
            if file.name != "icon_folder.png" and file.name != "status_bar_toggle_lock.png":
                shutil.copy2(file, drawable_dir / file.name) 