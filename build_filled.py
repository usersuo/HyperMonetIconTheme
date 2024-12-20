import time

from processors.cleaner import Cleaner
from processors.theme_packer import ThemePacker
from processors.usage_counter import UsageCounter
from processors.mapping_processor import MappingProcessor
from processors.fill_icon_processor import FillIconProcessor
from processors.fill_shortcut_processor import FillShortcutProcessor

from configs.config import (
    ApiConfig,
    IconConfig,
    CleanConfig,
    FillIconConfig,
    PerformanceConfig,
    ArtifactPathConfig,
    LawniconsPathConfig,
)


def build_filled(test_env: bool):
    print("test_env: ", test_env)
    
    # 运行前统计
    # UsageCounter.request_hits(ApiConfig.api_url_used, ApiConfig.api_headers)
    
    # 开始时间
    start_time = time.time()

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

    # 处理锁屏快捷方式
    print("\n(3/6) FillShortcutProcessor: 处理锁屏快捷方式")
    FillShortcutProcessor.process_lock_shortcut(
        str(LawniconsPathConfig.get_svg_dir(test_env)),
        str(ArtifactPathConfig.icons_template_dir),
        IconConfig.fg_color,
        IconConfig.bg_color,
        FillIconConfig(IconConfig.bg_color).fill_color,
        IconConfig.shortcut_icon_size,
        IconConfig.shortcut_icon_scale,
        PerformanceConfig.supersampling_scale,
    )

    # 处理图标
    print("\n(4/6) FillIconProcessor: 处理图标")
    FillIconProcessor.generate_icons(
        str(ArtifactPathConfig.icon_mapper),
        str(LawniconsPathConfig.get_svg_dir(test_env)),
        str(ArtifactPathConfig.output_dir),
        FillIconConfig(IconConfig.bg_color).fill_color,
        IconConfig.fg_color,
        IconConfig.bg_color,
        IconConfig.icon_size,
        IconConfig.icon_scale,
        PerformanceConfig.supersampling_scale,
        PerformanceConfig.max_workers,
        PerformanceConfig.batch_size_cv,
        PerformanceConfig.batch_size_normal,
        PerformanceConfig.array_pool_size,
        PerformanceConfig.fill_workers,
        PerformanceConfig.background_cache_size,
        PerformanceConfig.enable_fill_mask_cache
    )

    # 打包icons资源
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
        ArtifactPathConfig.target_magisk_pattern_filled,
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

    # 总耗时
    total_time = time.time() - start_time
    minutes = int(total_time // 60)
    seconds = total_time % 60
    print(f"\n运行总耗时: {minutes}分{seconds:.1f}秒")

    # 运行后统计
    # UsageCounter.request_hits(ApiConfig.api_url_succeed, ApiConfig.api_headers)


if __name__ == "__main__":
    build_filled(test_env=False)  # 是否使用测试目录
