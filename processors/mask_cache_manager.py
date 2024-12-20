import lz4.frame
import json
import tarfile
import numpy as np
import hashlib

from typing import Optional
from datetime import datetime
from pathlib import Path
from PIL import Image
from configs.config import PerformanceConfig


class MaskCacheManager:
    _cache_info = {}  # 用于存储缓存信息

    @classmethod
    def get_cache_path(cls, svg_path: str, size: int) -> Path:
        """获取缓存文件路径"""
        svg_name = Path(svg_path).stem

        # 基本文件名
        filename = f"{svg_name}_s{size}_ss{PerformanceConfig.supersampling_scale:.1f}"

        # 处理特殊情况
        if len(filename) > 200:  # 文件名过长
            path_hash = hashlib.md5(str(Path(svg_path).parent).encode()).hexdigest()[:8]
            filename = f"{svg_name[:50]}_{path_hash}_s{size}_ss{PerformanceConfig.supersampling_scale:.1f}"

        # 清理文件名
        filename = "".join(c for c in filename if c.isalnum() or c in "._-")

        return PerformanceConfig.fill_mask_cache_dir / f"{filename}.npmask"

    @classmethod
    def load_mask(cls, cache_path: Path) -> Optional[np.ndarray]:
        """加载mask缓存"""
        if not cache_path.exists():
            return None
        try:
            with open(cache_path, "rb") as f:
                compressed_data = f.read()
                mask_bytes = lz4.frame.decompress(compressed_data)
                mask = np.frombuffer(mask_bytes, dtype=np.uint8)
                size = int(np.sqrt(len(mask)))

                if size * size != len(mask):
                    print(f"    (warn) 缓存mask尺寸不匹配: {cache_path}")
                    return None

                try:
                    return mask.reshape(size, size)
                except ValueError as e:
                    print(f"    (warn) 重塑mask数组失败: {e}")
                    return None

        except Exception as e:
            print(f"    (err) 读取缓存失败 {cache_path}: {e}")
            return None

    @classmethod
    def save_mask(cls, mask: np.ndarray, cache_path: Path):
        """保存mask缓存"""
        try:
            if isinstance(mask, Image.Image):
                mask = np.array(mask)

            if len(mask.shape) > 2:
                mask = mask[:, :, 0]

            cache_path.parent.mkdir(parents=True, exist_ok=True)
            mask_bytes = mask.tobytes()
            compressed_data = lz4.frame.compress(mask_bytes)

            with open(cache_path, "wb") as f:
                f.write(compressed_data)

            relative_path = cache_path.relative_to(
                PerformanceConfig.fill_mask_cache_dir
            )
            cls._cache_info[str(relative_path)] = {
                "created_at": datetime.now().isoformat(),
                "size": len(compressed_data),
                "shape": mask.shape,
            }
        except Exception as e:
            print(f"    (err) 保存缓存失败: {e}")

    @classmethod
    def load_cache_info(cls):
        """加载缓存信息"""
        try:
            if PerformanceConfig.fill_mask_cache_info.exists():
                with open(PerformanceConfig.fill_mask_cache_info, "r") as f:
                    cls._cache_info = json.load(f)
        except Exception as e:
            print(f"    (err) 读取缓存信息失败: {e}")
            cls._cache_info = {}

    @classmethod
    def save_cache_info(cls):
        """保存缓存信息"""
        try:
            PerformanceConfig.fill_mask_cache_info.parent.mkdir(
                parents=True, exist_ok=True
            )
            with open(PerformanceConfig.fill_mask_cache_info, "w") as f:
                json.dump(cls._cache_info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"    (err) 保存缓存信息失败: {e}")

    @classmethod
    def pack_cache_files(cls):
        """打包缓存文件"""
        try:
            if not PerformanceConfig.fill_mask_cache_dir.exists():
                return

            print("    (cache) MaskCacheManager.pack_cache_files: 正在打包填充蒙版预计算缓存...")
            temp_tar = PerformanceConfig.fill_mask_cache_archive.with_suffix(".tar")

            with tarfile.open(temp_tar, "w") as tar:
                for mask_file in PerformanceConfig.fill_mask_cache_dir.glob("*.npmask"):
                    tar.add(
                        mask_file,
                        arcname=str(
                            mask_file.relative_to(PerformanceConfig.fill_mask_cache_dir)
                        ),
                    )

            with open(temp_tar, "rb") as f_in:
                with lz4.frame.open(
                    PerformanceConfig.fill_mask_cache_archive, "wb"
                ) as f_out:
                    f_out.write(f_in.read())

            temp_tar.unlink()
            print(f"    (cache) MaskCacheManager.pack_cache_files: 填充蒙版预计算缓存已打包至: {PerformanceConfig.fill_mask_cache_archive}")

        except Exception as e:
            print(f"    (err) 打包缓存文件失败: {e}")

    @classmethod
    def extract_cache_archive(cls):
        """解压缓存文件"""
        try:
            if not PerformanceConfig.fill_mask_cache_archive.exists():
                return

            print("    (cache) MaskCacheManager.extract_cache_archive: 正在解压填充蒙版预计算缓存 cached_masks.tar.lz4")
            PerformanceConfig.fill_mask_cache_dir.mkdir(parents=True, exist_ok=True)
            temp_tar = PerformanceConfig.fill_mask_cache_archive.with_suffix(".tar")

            with lz4.frame.open(
                PerformanceConfig.fill_mask_cache_archive, "rb"
            ) as f_in:
                with open(temp_tar, "wb") as f_out:
                    f_out.write(f_in.read())

            with tarfile.open(temp_tar, "r") as tar:
                tar.extractall(PerformanceConfig.fill_mask_cache_dir)

            temp_tar.unlink()
            print("    (cache) MaskCacheManager.extract_cache_archive: 填充蒙版预计算缓存解压完成")

        except Exception as e:
            print(f"    (err) 解压缓存文件失败: {e}")
