import shutil

from PIL import Image, ImageColor
from pathlib import Path

from processors.icon_processor import IconProcessor


# 快捷方式处理器
class ShortcutProcessor:
    @staticmethod
    def process_lock_shortcut(
        svg_dir: str,
        icons_template_dir: str,
        fg_color: str,
        bg_color: str,
        icon_size: int,
        icon_scale: float,
    ) -> None:
        print("  (1/1) 处理一键锁屏快捷方式")

        # 连续曲率圆角背景蒙版
        template_mod_icons = Path("templates/miui_mod_icons")

        drawable_dir = Path(icons_template_dir) / "res/drawable-xxhdpi"

        # 锁图标，使用volumelockr
        svg_path = Path(svg_dir) / "volumelockr.svg"

        drawable_dir.mkdir(parents=True, exist_ok=True)

        if not svg_path.exists():
            print("    (err) 未找到锁屏图标SVG文件")
            return

        background = Image.new("RGBA", (icon_size, icon_size), bg_color)

        icon = IconProcessor.process_svg(str(svg_path), fg_color, icon_size, icon_scale)

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
