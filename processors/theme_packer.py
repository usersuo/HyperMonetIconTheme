import os
import shutil
import zipfile

from pathlib import Path


class ThemePacker:
    """主题打包器

    用于打包图标主题资源：
    1. 打包图标资源
    2. 生成Magisk模块
    # 3. 生成MTZ主题包
    """

    @classmethod
    def pack_icons_zip(
        cls,
        output_dir: str,
        icons_template_dir: str,
        mtz_template_dir: str,
        magisk_template_dir: str,
    ) -> None:
        """打包图标资源为zip

        Args:
            output_dir: 图标输出目录
            icons_template_dir: 图标模板目录
            mtz_template_dir: MTZ模板目录
            magisk_template_dir: Magisk模板目录
        """
        icons_template_drawable_dir = (
            Path(icons_template_dir) / "res" / "drawable-xxhdpi"
        )

        # 移动所有图标到 icons 模板的 drawable-xxhdpi 目录
        # print("  (1/7) ThemePacker.pack_icons_zip: 从 output 移动图标到 icons_template")
        print("  (1/5) ThemePacker.pack_icons_zip: 从 output 移动图标到 icons_template")
        for item in Path(output_dir).iterdir():
            if item.is_dir():
                shutil.move(item, icons_template_drawable_dir / item.name)

        # 打包 icons 模板目录
        # print(
        #     "  (2/7) ThemePacker.pack_icons_zip: 正在使用 zipfile 封装 icons_template"
        # )
        print(
            "  (2/5) ThemePacker.pack_icons_zip: 正在使用 zipfile 封装 icons_template"
        )
        temp_icons_zip = Path(icons_template_dir) / "icons.zip"

        with zipfile.ZipFile(temp_icons_zip, "w", zipfile.ZIP_STORED) as zf:
            for root, dirs, files in os.walk(icons_template_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, icons_template_dir)
                    if os.path.getsize(file_path) > 0:  # 只添加非空文件
                        zf.write(file_path, arcname)

        # 重命名 icons.zip 为 icons, 拷贝到 mtz/magisk 模板
        # print("  (3/7) ThemePacker.pack_icons_zip: 合入 icons 到模板")
        print("  (3/5) ThemePacker.pack_icons_zip: 合入 icons 到模板")
        final_icons = Path(icons_template_dir) / "icons"
        os.rename(temp_icons_zip, final_icons)
        shutil.copy(final_icons, mtz_template_dir)
        shutil.copy(final_icons, magisk_template_dir)

    @classmethod
    def pack_magisk_module(
        cls,
        magisk_template_dir: str,
        target_magisk_pattern: str,
        timestamp: str,
        theme_suffix: str,
    ) -> None:
        """打包Magisk模块

        Args:
            magisk_template_dir: Magisk模板目录
            target_magisk_pattern: 目标文件名模式
            timestamp: 时间戳
            theme_suffix: 主题名称后缀
        """
        # print(
        #     "  (4/7) ThemePacker.pack_magisk_module: 正在使用 zipfile 封装 magisk_template_HyperOS2"
        # )
        print(
            "  (4/5) ThemePacker.pack_magisk_module: 正在使用 zipfile 封装 magisk_template_HyperOS2"
        )
        target_magisk = target_magisk_pattern.format(
            timestamp=timestamp, theme_suffix=theme_suffix
        )

        with zipfile.ZipFile(target_magisk, "w", zipfile.ZIP_STORED) as zf:
            for root, dirs, files in os.walk(magisk_template_dir):
                if "icons" in root:
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, magisk_template_dir)
                    zf.write(file_path, arcname)

        # print(
        #     f"  (5/7) ThemePacker.pack_magisk_module: magisk 模块已生成({target_magisk})"
        # )
        print(
            f"  (5/5) ThemePacker.pack_magisk_module: magisk 模块已生成({target_magisk})"
        )

    @classmethod
    def pack_mtz(
        cls,
        mtz_template_dir: str,
        target_mtz_pattern: str,
        timestamp: str,
        theme_suffix: str,
    ) -> None:
        """打包MTZ主题包

        Args:
            mtz_template_dir: MTZ模板目录
            target_pattern: 目标文件名模式
            timestamp: 时间戳
            theme_suffix: 主题名称后缀
        """
        print(
            "  (6/7) ThemePacker.pack_mtz: 正在使用 zipfile 封装 mtz_template_HyperOS2"
        )
        target_mtz = target_mtz_pattern.format(
            timestamp=timestamp, theme_suffix=theme_suffix
        )

        with zipfile.ZipFile(target_mtz, "w", zipfile.ZIP_STORED) as zf:
            for root, dirs, files in os.walk(mtz_template_dir):
                if "icons" in root:
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, mtz_template_dir)
                    zf.write(file_path, arcname)
        print(f"  (7/7) ThemePacker.pack_mtz: mtz 已生成({target_mtz})")
