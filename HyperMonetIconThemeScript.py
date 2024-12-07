from processors.mapping_processor import MappingProcessor
from processors.icon_processor import IconProcessor
from processors.theme_packer import ThemePacker
from processors.cleaner import Cleaner
from processors.usage_counter import UsageCounter
from configs.config import ThemeConfig, BuildConfig, PathConfig, ApiConfig, CleanConfig


def main():
    # 运行前统计
    UsageCounter.request_hits(ApiConfig.api_url_used, ApiConfig.api_headers)

    # 清理临时文件
    print("(1/5) Cleaner: 运行前清理")
    Cleaner.cleanup(CleanConfig.clean_up)

    # 处理映射
    print("\n(2/5) MappingProcessor: 处理映射")
    MappingProcessor.convert_icon_mapper(
        str(PathConfig.original_appfilter),
        str(PathConfig.icon_mapper),
        str(PathConfig.icon_mapper_alt)
    )

    # 处理图标
    print("\n(3/5) IconProcessor: 处理图标")
    IconProcessor.generate_icons(
        str(PathConfig.icon_mapper),
        str(PathConfig.svg_dir),
        str(PathConfig.output_dir),
        ThemeConfig.FG_COLOR,
        ThemeConfig.BG_COLOR,
        ThemeConfig.ICON_SIZE,
        ThemeConfig.ICON_SCALE,
        BuildConfig.MAX_WORKERS
    )

    # 打包icons
    print("\n(4/5) ThemePacker: 打包")
    ThemePacker.pack_icons_zip(
        str(PathConfig.output_dir),
        str(PathConfig.icons_template_dir),
        str(PathConfig.mtz_template_dir),
        str(PathConfig.magisk_template_dir)
    )

    # 打包magisk模块
    ThemePacker.pack_magisk_module(
        str(PathConfig.magisk_template_dir),
        PathConfig.target_magisk_pattern,
        PathConfig.timestamp,
        PathConfig.theme_suffix
    )

    # 打包mtz
    ThemePacker.pack_mtz(
        str(PathConfig.mtz_template_dir),
        PathConfig.target_mtz_pattern,
        PathConfig.timestamp,
        PathConfig.theme_suffix
    )

    # 运行后清理
    print("\n(5/5) Cleaner: 运行后清理")
    Cleaner.cleanup(CleanConfig.clean_up)

    print("\n处理完成, 工件已保存至当前目录")
    print("刷入后请重启设备")

    # 运行后统计
    UsageCounter.request_hits(ApiConfig.api_url_succeed, ApiConfig.api_headers)


if __name__ == "__main__":
    main()
