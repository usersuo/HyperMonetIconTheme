import os
from pathlib import Path
from datetime import datetime

# 当前工作目录
current_dir = Path.cwd()


# 主题配置
class ThemeConfig:
    # Material You Monet 配色, FG_COLOR前景色，为图标本体线条颜色；BG_COLOR背景色，为图标背景画布底色
    # 通常浅色模式下，FG_COLOR为深色，BG_COLOR为浅色；深色模式下，FG_COLOR为浅色，BG_COLOR为深色

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


# 构建配置
class BuildConfig:
    # 图标并行处理线程数
    # 最大128
    # None为默认，为CPU核心数的4倍。16核 = 64线程
    MAX_WORKERS = None


# 路径配置
class PathConfig:
    # lawnicons的原始映射文件
    # 测试目录
    original_appfilter = current_dir / "test" / "appfilter.xml"
    # 生产目录
    # original_appfilter = (
    #     current_dir / "lawnicons-develop" / "app" / "assets" / "appfilter.xml"
    # )

    # 处理后的映射文件
    icon_mapper = current_dir / "mappers" / "icon_mapper.xml"

    # 自定义映射文件
    # 用于新增自定义图标映射，请在icon_mapper_alt.xml中按格式添加
    icon_mapper_alt = current_dir / "mappers" / "icon_mapper_alt.xml"

    # SVG源文件
    # 测试目录
    svg_dir = current_dir / "test" / "svgs"
    # 生产目录
    # svg_dir = current_dir / "lawnicons-develop" / "svgs"

    # 图标临时输出目录
    output_dir = current_dir / "output"

    # 模板目录
    icons_template_dir = current_dir / "templates" / "icons_template"
    mtz_template_dir = current_dir / "templates" / "mtz_template_HyperOS"
    magisk_template_dir = current_dir / "templates" / "magisk_template_HyperOS"

    # 时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 主题名称
    theme_name = os.getenv("THEME_NAME", "")
    theme_suffix = f"_{theme_name}" if theme_name else ""

    # 输出文件名模式
    target_mtz_pattern = str(
        current_dir / f"mtz_HyperMonetIcon{theme_suffix}_{timestamp}.mtz"
    )
    target_magisk_pattern = str(
        current_dir / f"magisk_HyperMonetIcon{theme_suffix}_{timestamp}.zip"
    )


# 清理配置
class CleanConfig:
    # 清理目录
    clean_up = [
        current_dir / "output",
        current_dir / "templates" / "icons_template" / "res" / "drawable-xxhdpi",
        current_dir / "templates" / "icons_template" / "icons.zip",
        current_dir / "templates" / "icons_template" / "icons",
        current_dir / "templates" / "mtz_template_HyperOS" / "icons",
        current_dir / "templates" / "magisk_template_HyperOS" / "icons",
        current_dir / "mappers" / "icon_mapper.xml",
        current_dir / "processors" / "__pycache__",
        current_dir / "configs" / "__pycache__",
    ]


# 反馈API配置
class ApiConfig:
    # 运行次数反馈
    # 用于Github readme统计标签
    # https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-used
    # https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-succeed
    api_url_used = f"https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-used.svg"
    api_url_succeed = (
        f"https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-succeed.svg"
    )
    api_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
    }
