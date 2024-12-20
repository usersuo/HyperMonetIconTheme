from processors.cleaner import Cleaner
from processors.theme_packer import ThemePacker
from processors.usage_counter import UsageCounter
from processors.icon_processor import IconProcessor
from processors.mapping_processor import MappingProcessor
from processors.shortcut_processor import ShortcutProcessor

from configs.config import (
    ApiConfig,
    IconConfig,
    CleanConfig,
    PerformanceConfig,
    ArtifactPathConfig,
    LawniconsPathConfig,
)


def build_outlined(test_env: bool):
    print("test_env: ", test_env)

    # 运行前统计
    UsageCounter.request_hits(ApiConfig.api_url_used, ApiConfig.api_headers)

    # 清理临时文件
    print("(1/6) Cleaner: 运行前清理")
    Cleaner.cleanup(CleanConfig.clean_up)

    # 处理映射
    print("\n(2/6) MappingProcessor: 处理映射")
    MappingProcessor.convert_icon_mapper(
        str(LawniconsPathConfig.get_appfilter(test_env)),
        str(ArtifactPathConfig.icon_mapper),
        str(ArtifactPathConfig.icon_mapper_alt),
    )

    print("\n(3/6) IconProcessor: 处理快捷方式图标")
    ShortcutProcessor.process_lock_shortcut(
        str(LawniconsPathConfig.get_svg_dir(test_env)),
        str(ArtifactPathConfig.icons_template_dir),
        IconConfig.fg_color,
        IconConfig.bg_color,
        IconConfig.shortcut_icon_size,
        IconConfig.shortcut_icon_scale,
    )

    # 处理图标
    print("\n(4/6) IconProcessor: 处理图标")
    IconProcessor.generate_icons(
        str(ArtifactPathConfig.icon_mapper),
        str(LawniconsPathConfig.get_svg_dir(test_env)),
        str(ArtifactPathConfig.output_dir),
        IconConfig.fg_color,
        IconConfig.bg_color,
        IconConfig.icon_size,
        IconConfig.icon_scale,
        PerformanceConfig.max_workers,
    )

    # 打包icons
    print("\n(5/6) ThemePacker: 打包")
    ThemePacker.pack_icons_zip(
        str(ArtifactPathConfig.output_dir),
        str(ArtifactPathConfig.icons_template_dir),
        str(ArtifactPathConfig.mtz_template_dir),
        str(ArtifactPathConfig.magisk_template_dir),
    )

    # 打包magisk模块
    ThemePacker.pack_magisk_module(
        str(ArtifactPathConfig.magisk_template_dir),
        ArtifactPathConfig.target_magisk_pattern_outlined,
        ArtifactPathConfig.timestamp,
        ArtifactPathConfig.theme_suffix,
    )

    # 打包mtz
    # ThemePacker.pack_mtz(
    #     str(ArtifactPathConfig.mtz_template_dir),
    #     ArtifactPathConfig.target_mtz_pattern,
    #     ArtifactPathConfig.timestamp,
    #     ArtifactPathConfig.theme_suffix,
    # )

    # 运行后清理
    print("\n(6/6) Cleaner: 运行后清理")
    Cleaner.cleanup(CleanConfig.clean_up)

    print("\n处理完成, 工件已保存至当前目录")
    print("刷入后请重启设备")

    # 运行后统计
    UsageCounter.request_hits(ApiConfig.api_url_succeed, ApiConfig.api_headers)


if __name__ == "__main__":
    build_outlined(test_env=False)  # 是否使用测试目录
