import os
import threading
import functools
import hashlib
import numpy as np
import time

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageColor, ImageDraw, ImageFilter

from processors.icon_processor import IconProcessor
from configs.config import PerformanceConfig

try:
    import cv2

    USE_CV = True
    print("OpenCV: 已启用 OpenCV 优化")
except:
    USE_CV = False
    print("OpenCV: 未检测到 OpenCV, 使用原始处理方式")


# 填充图标处理器
class FillIconProcessor:
    counter_lock = threading.Lock()
    processed_count = 0
    _array_pool = []
    _pool_lock = threading.Lock()
    _start_time = 0.0
    _last_update_time = 0.0
    _last_count = 0

    @classmethod
    def get_array(cls, shape, dtype=np.uint8):
        with cls._pool_lock:
            if cls._array_pool:
                arr = cls._array_pool.pop()
                if arr.shape == shape and arr.dtype == dtype:
                    arr.fill(0)
                    return arr
            return np.zeros(shape, dtype)

    @classmethod
    def release_array(cls, arr):
        with cls._pool_lock:
            if len(cls._array_pool) < PerformanceConfig.array_pool_size:
                cls._array_pool.append(arr)

    @classmethod
    def increment_counter(cls) -> int:
        with cls.counter_lock:
            cls.processed_count += 1
            return cls.processed_count

    # 处理进度
    @classmethod
    def update_progress(
        cls, count: int, total: int, drawable_name: str, package_name: str
    ):
        current_time = time.time()

        if cls._start_time == 0:
            cls._start_time = current_time
            cls._last_update_time = current_time
            cls._last_count = 0
            return

        time_diff = current_time - cls._last_update_time
        if time_diff >= 1.0:
            count_diff = count - cls._last_count
            speed = count_diff / time_diff
            total_time = current_time - cls._start_time
            avg_speed = count / total_time if total_time > 0 else 0
            remaining = (total - count) / speed if speed > 0 else 0
            percentage = (count / total) * 100

            print(
                f"\r    ({count}/{total}) {percentage:.1f}% "
                f"[{speed:.1f}个/秒 | 平均{avg_speed:.1f}个/秒 | 预计剩余{remaining:.1f}秒] "
                f"- {drawable_name} ({package_name})" + " " * 20,
                end="",
                flush=True,
            )

            cls._last_update_time = current_time
            cls._last_count = count
        else:
            percentage = (count / total) * 100
            print(
                f"\r    ({count}/{total}) {percentage:.1f}% "
                f"- {drawable_name} ({package_name})" + " " * 20,
                end="",
                flush=True,
            )

    @classmethod
    def get_cached_background_impl(cls, icon_size: int, color: str) -> Image.Image:
        return Image.new("RGBA", (icon_size, icon_size), color)

    @classmethod
    def get_cached_background(cls, icon_size: int, color: str) -> Image.Image:
        return cls.get_cached_background_impl(icon_size, color)

    # SVG 处理缓存
    @classmethod
    def get_cached_svg(
        cls, svg_path: str, fg_color: str, size: int, scale: float
    ) -> Image.Image:
        cache_key = f"{svg_path}_{fg_color}_{size}_{scale}"
        cache_path = f".cache/{hashlib.md5(cache_key.encode()).hexdigest()}.png"

        if os.path.exists(cache_path):
            return Image.open(cache_path)

        icon = IconProcessor.process_svg(svg_path, fg_color, size, scale)
        if icon:
            os.makedirs(".cache", exist_ok=True)
            icon.save(cache_path)
        return icon

    # 处理单个图标
    @classmethod
    def process_single_icon(
        cls,
        package_name: str,
        drawable_name: str,
        svg_dir: Path,
        output_dir: Path,
        background: Image.Image,
        fg_color: str,
        fill_color: str,
        icon_size: int,
        icon_scale: float,
        supersampling_scale: int,
        total_icons: int,
        fill_array: np.ndarray,
        fill_workers: int,
    ) -> bool:
        svg_path = svg_dir / f"{drawable_name}.svg"

        if not svg_path.exists():
            print(
                f"    (err) FillIconProcessor.generate_icons: 未找到对应svg文件 {drawable_name} ({package_name})"
            )
            return False

        icon_dir = output_dir / package_name
        icon_dir.mkdir(exist_ok=True)

        background.save(icon_dir / "0.png", "PNG")

        # 超采样尺寸
        ss_size = int(icon_size * supersampling_scale)
        ss_scale = icon_scale

        line_icon = cls.get_cached_svg(str(svg_path), fg_color, ss_size, ss_scale)
        if not line_icon:
            print(
                f"    (err) FillIconProcessor.generate_icons: 处理线条失败 {drawable_name} ({package_name})"
            )
            return False

        fill_layer = Image.new("RGBA", line_icon.size, (0, 0, 0, 0))
        fill_color_rgba = ImageColor.getrgb(fill_color)

        # OpenCV 优化的图像处理
        if USE_CV:
            cv_image = np.array(line_icon)
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGBA2BGR)

            smoothed = cv2.GaussianBlur(cv_image, (5, 5), 0.8)

            # 转换为灰度图并二值化
            gray = cv2.cvtColor(smoothed, cv2.COLOR_BGR2GRAY)
            binary_mask = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)[1]

            kernel = np.ones((3, 3), np.uint8)
            binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)

            # 转回 PIL 格式
            binary_mask = Image.fromarray(binary_mask)
        else:
            # 原始处理方式
            smoothed = line_icon.filter(ImageFilter.GaussianBlur(0.8))
            binary_mask = smoothed.convert("L").point(lambda x: 255 if x > 20 else 0)

        # 填充点选择
        width, height = binary_mask.size
        start_points = [
            (0, 0),
            (width - 1, 0),
            (0, height - 1),
            (width - 1, height - 1),  # 四角
            (width // 2, 0),
            (width // 2, height - 1),
            (0, height // 2),
            (width - 1, height // 2),  # 边中点
        ]

        # 填充处理
        if USE_CV:
            fill_array = np.array(binary_mask)
            mask = np.zeros(
                (fill_array.shape[0] + 2, fill_array.shape[1] + 2), np.uint8
            )

            # 处理填充点
            with ThreadPoolExecutor(max_workers=fill_workers) as executor:
                futures = []
                for x, y in start_points:
                    futures.append(
                        executor.submit(
                            cv2.floodFill, fill_array, mask.copy(), (x, y), 128
                        )
                    )
                for future in futures:
                    future.result()

            fill_array = np.where((fill_array != 128) & (fill_array != 255), 255, 0)
            fill_mask = Image.fromarray(fill_array.astype("uint8"))
        else:
            fill_mask = binary_mask.filter(ImageFilter.SMOOTH_MORE).point(
                lambda x: 255 if x > 128 else 0
            )
            for x, y in start_points:
                ImageDraw.floodfill(fill_mask, (x, y), 128)

        fill_pixels = fill_layer.load()
        mask_pixels = fill_mask.load()
        for y in range(height):
            for x in range(width):
                if mask_pixels[x, y] == 255:
                    fill_pixels[x, y] = fill_color_rgba

        final_icon = Image.alpha_composite(fill_layer, line_icon)

        final_icon = final_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

        final_icon.save(icon_dir / "1.png", "PNG")

        count = cls.increment_counter()
        cls.update_progress(count, total_icons, drawable_name, package_name)
        return True

    # 处理全部图标
    @classmethod
    def generate_icons(
        cls,
        icon_mapper_path: str,
        svg_dir: str,
        output_dir: str,
        fill_color: str,
        fg_color: str,
        bg_color: str,
        icon_size: int,
        icon_scale: float,
        supersampling_scale: int,
        max_workers: int,
        batch_size_cv: int,
        batch_size_normal: int,
        array_pool_size: int,
        fill_workers: int,
        background_cache_size: int,
    ) -> None:
        cls.processed_count = 0
        cls._start_time = 0.0
        cls._last_update_time = 0.0
        cls._last_count = 0

        cls._array_pool_size = array_pool_size

        cls.get_cached_background = functools.lru_cache(maxsize=background_cache_size)(
            cls.get_cached_background_impl
        )

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        svg_dir_path = Path(svg_dir)

        mapper = IconProcessor.parse_icon_mapper(icon_mapper_path)

        print(f"  (2/4) FillIconProcessor.generate_icons: 创建 {bg_color} 背景")
        background = cls.get_cached_background(icon_size, bg_color)

        max_workers = max_workers

        total_icons = len(mapper)
        print(
            f"  (3/4) FillIconProcessor.generate_icons: 找到 {total_icons} 个图标需要理，当前并行线程数 {max_workers}"
        )

        batch_size = batch_size_cv if USE_CV else batch_size_normal

        arrays = [cls.get_array((icon_size, icon_size)) for _ in range(batch_size)]

        successful = 0

        try:
            for i in range(0, total_icons, batch_size):
                batch_items = list(mapper.items())[i : i + batch_size]

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = []
                    for idx, (package_name, drawable_name) in enumerate(batch_items):
                        futures.append(
                            executor.submit(
                                cls.process_single_icon,
                                package_name,
                                drawable_name,
                                svg_dir_path,
                                output_path,
                                background,
                                fg_color,
                                fill_color,
                                icon_size,
                                icon_scale,
                                supersampling_scale,
                                total_icons,
                                arrays[idx],
                                fill_workers,
                            )
                        )

                    for future in futures:
                        try:
                            if future.result():
                                successful += 1
                        except Exception as e:
                            print(f"\n    (err) 处理图标时发生错误: {e}")
        finally:
            for arr in arrays:
                cls.release_array(arr)

        print(
            f"\n  (4/4) FillIconProcessor.generate_icons: 图标处理完成，成功处理 {successful}/{total_icons}"
        )
