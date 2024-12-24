import shutil

from PIL import Image
from pathlib import Path

from processors.outline_icon_processor import OutlineIconProcessor


class OutlinedShortcutProcessor:
    """Outlined风格快捷方式处理器

    用于生成Outlined风格的锁屏快捷方式图标
    1. 单层PNG输出
    2. 圆角蒙版
    3. 不使用多线程
    """

    @classmethod
    def process_lock_shortcut(
        cls,
        svg_dir: str,
        icons_template_dir: str,
        fg_color: str,
        bg_color: str,
        icon_size: int,
        icon_scale: float,
    ) -> None:
        """处理锁屏快捷方式图标

        Args:
            svg_dir: SVG源文件目录
            icons_template_dir: 图标模板目录
            fg_color: 前景色
            bg_color: 背景色
            icon_size: 图标尺寸
            icon_scale: 图标缩放比例
        """
        print("  (1/1) 处理一键锁屏快捷方式")

        # 连续曲率圆角背景蒙版
        template_mod_icons = Path("templates/miui_mod_icons")

        drawable_dir = Path(icons_template_dir) / "res/drawable-xxhdpi"

        # 锁图标, 使用volumelockr图标
        svg_path = Path(svg_dir) / "volumelockr.svg"

        drawable_dir.mkdir(parents=True, exist_ok=True)

        if not svg_path.exists():
            print("    (err) 未找到锁屏图标SVG文件")
            return

        background = Image.new("RGBA", (icon_size, icon_size), bg_color)

        icon = OutlineIconProcessor.process_svg(str(svg_path), fg_color, icon_size, icon_scale)

        if not icon:
            print("    (err) 处理锁屏图标失败")
            return

        mask_path = template_mod_icons / "icon_folder.png"
        output_path = drawable_dir / "status_bar_toggle_lock.png"

        if not mask_path.exists():
            print(f"    (err) 未找到蒙版文件: {mask_path}")
            return

        mask = Image.open(mask_path).convert("L")
        mask = mask.resize((icon_size, icon_size))

        # 应用蒙版到背景
        background_copy = background.copy()
        background_copy.putalpha(mask)

        # 合并图层
        final_image = Image.alpha_composite(background_copy, icon)

        final_image.save(output_path, "PNG")
        print(f"    (1/1) 处理完成: {output_path}")

        for file in template_mod_icons.glob("*.png"):
            if (
                file.name != "icon_folder.png"
                and file.name != "status_bar_toggle_lock.png"
            ):
                shutil.copy2(file, drawable_dir / file.name)
