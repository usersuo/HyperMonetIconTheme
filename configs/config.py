import os
import colorsys

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime


# 当前工作目录
current_dir = Path.cwd()


# 性能调优配置
# 预计处理图标数量：7400+
# 普通样式图标：预计构建时间 5 分钟，预计打包大小 50 MB
# 填充样式图标：预计构建时间 10 分钟，预计打包大小 110 MB
@dataclass
class PerformanceConfig:
    # (全部样式生效) 线程配置，同时处理max_workers个图标
    max_workers: int = min(128, (os.cpu_count() or 1) * 8)

    # (仅填充样式生效) 批处理大小，一次读入batch_size个图标供max_workers处理
    batch_size_cv: int = 512  # OpenCV优化的批处理大小
    batch_size_normal: int = 256  # 普通模式的批处理大小

    # (仅填充样式生效) 单个图标起始填充点并行数量
    fill_workers: int = min(4, (os.cpu_count() or 1))

    # (仅填充样式生效) NumPy 内存池大小
    array_pool_size: int = 512

    # (仅填充样式生效) 背景缓存数量
    background_cache_size: int = 4

    # (仅填充样式生效) 超采样倍数，避免填充锯齿。越大越慢
    supersampling_scale: float = 1.5


# 普通图标配置
@dataclass
class IconConfig:
    # Material You Monet 配色, fg_color前景色，图标本体线条颜色；bg_color背景色，为图标背景画布底色
    # 通常浅色模式下，fg_color为深色，bg_color为浅色；深色模式下，fg_color为浅色，bg_color为深色

    # 深色主题 蓝色
    # fg_color: str = "#d1e2fc" # 前景色
    # bg_color: str = "#1c232b" # 背景色

    fg_color: str = "#003a71"
    bg_color: str = "#a1cafe"

    # 浅色主题 蓝色
    # fg_color: str  = "#011c31"
    # bg_color: str  = "#e8ecf7"

    # 深色主题 红色
    # fg_color: str  = "#fcdbcf"
    # bg_color: str  = "#2d2017"

    # 浅色主题 红色
    # fg_color: str  = "#331300"
    # bg_color: str  = "#f5eae4"

    # 深色主题 绿色
    # fg_color: str  = "#c7efac"
    # bg_color: str  = "#1e241a"

    # 浅色主题 绿色
    # fg_color: str  = "#071e02"
    # bg_color: str  = "#eaeee0"

    # 浅色 白 加速构建
    # fg_color: str  = "#000000"
    # bg_color: str  = "#ffffff"

    # 图标大小和缩放比例
    # HyperOS图标（和背景）最大为432*432，且系统会对图标本体前景）四周进行33.3%的裁切
    # 66.6%缩放可预留裁切空间，此时为432*66.6%=288，铺满背景画布，图标过大
    # 按40%缩放，最终图标本体长宽为432*40%=172，效果最佳，不至于铺满背景画布
    icon_size: int = 432  # 图标大小432*432
    icon_scale: float = 0.4  # 图标占未裁切背景画布的40%

    # 快捷方式图标大小和缩放比例
    # 快捷方式图标不裁切，单个带圆角png图标，不分层
    shortcut_icon_size: int = 235
    shortcut_icon_scale: float = 0.6


# 图标填充颜色
class FillIconConfig:
    def __init__(self, bg_color: str):
        self.bg_color = bg_color

    @property
    def fill_color(self) -> str:
        bg_rgb = tuple(int(self.bg_color[i : i + 2], 16) / 255.0 for i in (1, 3, 5))
        bg_h, bg_l, bg_s = colorsys.rgb_to_hls(*bg_rgb)

        is_pure_white = all(c > 0.99 for c in bg_rgb)
        is_near_white = bg_l > 0.8 and bg_s < 0.5
        is_near_dark = bg_l < 0.5

        if is_near_white:
            fill_l = min(0.95, bg_l * 0.85)
            fill_s = max(0.3, bg_s * 1.15)
            fill_h = bg_h
        elif is_near_dark:
            fill_l = min(0.95, bg_l * 3)
            fill_s = max(0.1, bg_s * 0.8)
            fill_h = bg_h
        else:
            brightness_factor = 1 + (1 - bg_l)
            fill_l = min(0.95, bg_l * brightness_factor)
            saturation_factor = 0.8 if bg_s > 0.5 else 0.6
            fill_s = max(0.1, bg_s * saturation_factor)
            fill_h = bg_h

        fill_rgb = colorsys.hls_to_rgb(fill_h, fill_l, fill_s)
        return f"#{int(fill_rgb[0]*255):02x}{int(fill_rgb[1]*255):02x}{int(fill_rgb[2]*255):02x}"


# Lawnicons路径配置
class LawniconsPathConfig:
    # 测试目录
    test_appfilter: Path = current_dir / "test" / "appfilter.xml"
    test_svg_dir: Path = current_dir / "test" / "svgs"

    # 生产目录
    prod_appfilter: Path = (
        current_dir / "lawnicons-develop" / "app" / "assets" / "appfilter.xml"
    )
    prod_svg_dir: Path = current_dir / "lawnicons-develop" / "svgs"

    @classmethod
    def get_appfilter(cls, test_env: bool = True) -> Path:
        return cls.test_appfilter if test_env else cls.prod_appfilter

    @classmethod
    def get_svg_dir(cls, test_env: bool = True) -> Path:
        return cls.test_svg_dir if test_env else cls.prod_svg_dir


# 工件路径配置
@dataclass
class ArtifactPathConfig:
    # 处理后的映射文件
    icon_mapper: Path = current_dir / "mappers" / "icon_mapper.xml"

    # 自定义映射文件
    # 用于新增自定义图标映射，请在icon_mapper_alt.xml中按格式添加
    icon_mapper_alt: Path = current_dir / "mappers" / "icon_mapper_alt.xml"

    # 图标临时输出目录
    output_dir: Path = current_dir / "output"

    # 模板目录
    icons_template_dir: Path = current_dir / "templates" / "icons_template"
    mtz_template_dir: Path = current_dir / "templates" / "mtz_template_HyperOS"
    magisk_template_dir: Path = current_dir / "templates" / "magisk_template_HyperOS"

    # 时间戳
    timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 主题名称
    theme_name: str = os.getenv("THEME_NAME", "")
    theme_suffix: str = f"_{theme_name}" if theme_name else ""

    # 输出文件名式
    target_mtz_pattern: str = str(
        current_dir / f"mtz_HyperMonetIcon{theme_suffix}_{timestamp}.mtz"
    )
    target_magisk_pattern_filled: str = str(
        current_dir / f"magisk_HyperMonetIcon_filled_{theme_suffix}_{timestamp}.zip"
    )
    target_magisk_pattern_outlined: str = str(
        current_dir / f"magisk_HyperMonetIcon_outlined_{theme_suffix}_{timestamp}.zip"
    )


# 清理配置
class CleanConfig:
    # 清理目录
    clean_up: list = [
        current_dir / "output",
        current_dir / "templates" / "icons_template" / "res" / "drawable-xxhdpi",
        current_dir / "templates" / "icons_template" / "icons.zip",
        current_dir / "templates" / "icons_template" / "icons",
        current_dir / "templates" / "mtz_template_HyperOS" / "icons",
        current_dir / "templates" / "magisk_template_HyperOS" / "icons",
        current_dir / "mappers" / "icon_mapper.xml",
        current_dir / "processors" / "__pycache__",
        current_dir / "configs" / "__pycache__",
        current_dir / ".cache",
    ]


# 运行次数反馈
class ApiConfig:
    api_url_used: str = (
        "https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-used.svg"
    )
    api_url_succeed: str = (
        "https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-succeed.svg"
    )
    api_headers: dict = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
    }
