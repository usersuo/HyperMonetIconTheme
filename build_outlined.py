import time
import os
import argparse

from processors.cleaner import Cleaner
from processors.theme_packer import ThemePacker
from processors.usage_counter import UsageCounter
from processors.mapping_processor import MappingProcessor
from processors.outline_icon_processor import OutlineIconProcessor
from processors.outline_shortcut_processor import OutlinedShortcutProcessor

from configs.config import (
    ApiConfig,
    IconConfig,
    CleanConfig,
    PerformanceConfig,
    ArtifactPathConfig,
    LawniconsPathConfig,
)

def parse_args():
    """解析命令行参数
    
    支持的参数: 
        -fg: 前景色, 例如 "#003a71"
        -bg: 背景色, 例如 "#a1cafe"
        -test: 是否使用测试目录, 默认False
    
    Example:
        使用生产目录:
            python build_outlined.py -fg "#003a71" -bg "#a1cafe"
        使用测试目录:
            python build_outlined.py -fg "#003a71" -bg "#a1cafe" -test
    """
    parser = argparse.ArgumentParser(description='构建Outlined风格图标')
    parser.add_argument('-fg', type=str, help='前景色 (例如: "#003a71")')
    parser.add_argument('-bg', type=str, help='背景色 (例如: "#a1cafe")')
    parser.add_argument('-test', action='store_true', help='使用test测试目录')
    return parser.parse_args()


def build_outlined(test_env: bool):
    """构建Outlined风格图标主题

    用于构建Outlined风格的图标主题
        1. 清理临时文件
        2. 处理图标映射
        3. 处理锁屏快捷方式
        4. 处理应用图标
        5. 打包图标资源
        6. 打包Magisk模块
        7. 清理临时文件

    Args:
        test_env: 是否使用测试环境
            True: 使用test/目录下的测试文件
            False: 使用lawnicons-develop/的完整文件

    工件输出:
        - ./magisk_HyperMonetIcon_outlined_{theme_name}_{timestamp}.zip
    """
    print("test_env: ", test_env)

    # 运行前统计
    UsageCounter.request_hits(ApiConfig.api_url_used, ApiConfig.api_headers)

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
    print("\n(3/6) OutlineIconProcessor: 处理锁屏快捷方式")
    OutlinedShortcutProcessor.process_lock_shortcut(
        str(LawniconsPathConfig.get_svg_dir(test_env)),
        str(ArtifactPathConfig.icons_template_dir),
        IconConfig.fg_color,
        IconConfig.bg_color,
        IconConfig.shortcut_icon_size,
        IconConfig.shortcut_icon_scale,
    )

    # 处理图标
    print("\n(4/6) OutlineIconProcessor: 处理图标")
    OutlineIconProcessor.generate_icons(
        str(ArtifactPathConfig.icon_mapper),
        str(LawniconsPathConfig.get_svg_dir(test_env)),
        str(ArtifactPathConfig.output_dir),
        IconConfig.fg_color,
        IconConfig.bg_color,
        IconConfig.icon_size,
        IconConfig.icon_scale,
        PerformanceConfig.max_workers,
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
        ArtifactPathConfig.target_magisk_pattern_outlined,
        ArtifactPathConfig.timestamp,
        ArtifactPathConfig.theme_suffix,
    )

    # # 打包mtz
    # ThemePacker.pack_mtz(
    #     str(ArtifactPathConfig.mtz_template_dir),
    #     ArtifactPathConfig.target_mtz_pattern_outlined,
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
    UsageCounter.request_hits(ApiConfig.api_url_succeed, ApiConfig.api_headers)

if __name__ == "__main__":
    args = parse_args()
    
    # 优先使用命令行参数, 其次使用环境变量
    if args.fg:
        IconConfig.fg_color = args.fg
    elif os.getenv("FG_COLOR"):
        IconConfig.fg_color = os.getenv("FG_COLOR")
        
    if args.bg:
        IconConfig.bg_color = args.bg
    elif os.getenv("BG_COLOR"):
        IconConfig.bg_color = os.getenv("BG_COLOR")
        
    # 是否使用测试目录
    test_env = args.test or os.getenv("TEST_ENV", "False").lower() == "true"
    build_outlined(test_env=test_env)
