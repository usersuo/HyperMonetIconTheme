import lz4.frame
import tarfile
import numpy as np
import hashlib
import yaml

from typing import Optional
from datetime import datetime
from pathlib import Path
from PIL import Image
from configs.config import PerformanceConfig


class MaskCacheManager:
    """填充蒙版预计算缓存管理器
    
    管理图标填充区域的二值化mask缓存
    缓存元数据列表yml存储, 二值化mask数据lz4压缩存储, 均位于current_dir。
    """

    # 缓存元数据
    _cache_info = {
        "metadata": {
            "version": "1.0.0",  # 缓存版本号
            "created_at": "",  # 首次创建时间
            "updated_at": "",  # 最后更新时间
            "total_masks": 0,  # 总缓存数量
            "total_size": 0,  # 总缓存大小(bytes)
            "supersampling_scale": float(PerformanceConfig.supersampling_scale),
        },
        "masks": {},
    }

    @classmethod
    def get_cache_path(cls, svg_path: str, size: int) -> Path:
        """根据SVG路径和尺寸生成缓存文件路径

        Args:
            svg_path: SVG文件路径
            size: 图标尺寸(超采样后)

        Returns:
            Path: 缓存文件路径, 格式为"{svg_name}_s{size}_ss{scale}.npmask"
        """
        svg_name = Path(svg_path).stem

        # 基本文件名
        filename = f"{svg_name}_s{size}_ss{PerformanceConfig.supersampling_scale:.1f}"

        # 处理特殊情况
        if len(filename) > 200:  # 文件名过长
            path_hash = hashlib.md5(str(Path(svg_path).parent).encode()).hexdigest()[:8]
            filename = f"{svg_name[:50]}_{path_hash}_s{size}_ss{PerformanceConfig.supersampling_scale:.1f}"

        filename = "".join(c for c in filename if c.isalnum() or c in "._-")

        return PerformanceConfig.fill_mask_cache_dir / f"{filename}.npmask"

    @classmethod
    def load_mask(cls, cache_path: Path) -> Optional[np.ndarray]:
        """从缓存文件加载mask数据

        Args:
            cache_path: 缓存文件路径

        Returns:
            np.ndarray | None: 成功返回numpy数组形式的mask, 失败返回None
        """
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
        """保存mask数据到缓存文件

        Args:
            mask: 要缓存的mask数组
            cache_path: 缓存文件路径
        
        保存的同时会更新cache_info中的元数据和具体mask信息
        """
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

            # 更新具体mask信息
            cls._cache_info["masks"][str(relative_path)] = {
                "created_at": datetime.now().isoformat(),
                "file_size": len(compressed_data),
                "original_size": mask.nbytes,
                "compression_ratio": f"{mask.nbytes / len(compressed_data):.2f}",
                "shape": [*mask.shape],
                "dtype": str(mask.dtype),
                "hash": hashlib.md5(compressed_data).hexdigest(),
            }

            # 更新元数据
            cls._cache_info["metadata"].update(
                {
                    "updated_at": datetime.now().isoformat(),
                    "total_masks": len(cls._cache_info["masks"]),
                    "total_size": sum(
                        m["file_size"] for m in cls._cache_info["masks"].values()
                    ),
                    "supersampling_scale": float(PerformanceConfig.supersampling_scale),
                }
            )

        except Exception as e:
            print(f"    (err) 保存缓存失败: {e}")

    @classmethod
    def load_cache_info(cls):
        """加载缓存信息文件

        从YAML文件加载缓存元数据和具体mask信息
        如果文件不存在则初始化新的缓存信息
        """
        try:
            if PerformanceConfig.fill_mask_cache_info.exists():
                with open(
                    PerformanceConfig.fill_mask_cache_info, "r", encoding="utf-8"
                ) as f:
                    cls._cache_info = yaml.safe_load(f) or {}
                    # 确保metadata存在并包含所有必要字段
                    if "metadata" not in cls._cache_info:
                        cls._cache_info["metadata"] = {}

                    # 更新或初始化metadata
                    cls._cache_info["metadata"].update(
                        {
                            "version": cls._cache_info["metadata"].get(
                                "version", "1.0.0"
                            ),
                            "created_at": cls._cache_info["metadata"].get(
                                "created_at", datetime.now().isoformat()
                            ),
                            "updated_at": datetime.now().isoformat(),
                            "total_masks": len(cls._cache_info.get("masks", {})),
                            "total_size": sum(
                                m.get("file_size", 0)
                                for m in cls._cache_info.get("masks", {}).values()
                            ),
                            "supersampling_scale": float(
                                PerformanceConfig.supersampling_scale
                            ),
                        }
                    )

                    if "masks" not in cls._cache_info:
                        cls._cache_info["masks"] = {}
            else:
                # 初始化新的缓存信息
                cls._cache_info = {
                    "metadata": {
                        "version": "1.0.0",
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat(),
                        "total_masks": 0,
                        "total_size": 0,
                        "supersampling_scale": float(
                            PerformanceConfig.supersampling_scale
                        ),
                    },
                    "masks": {},
                }
        except Exception as e:
            print(f"    (err) 读取缓存信息失败: {e}")
            cls._cache_info = {
                "metadata": {
                    "version": "1.0.0",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "total_masks": 0,
                    "total_size": 0,
                    "supersampling_scale": float(PerformanceConfig.supersampling_scale),
                },
                "masks": {},
            }

    @classmethod
    def save_cache_info(cls):
        """保存缓存信息到YAML文件

        将当前的缓存元数据和具体mask信息保存到文件
        """
        try:
            PerformanceConfig.fill_mask_cache_info.parent.mkdir(
                parents=True, exist_ok=True
            )
            with open(
                PerformanceConfig.fill_mask_cache_info, "w", encoding="utf-8"
            ) as f:
                yaml.dump(
                    cls._cache_info, f, allow_unicode=True, sort_keys=False, indent=2
                )
        except Exception as e:
            print(f"    (err) 保存缓存信息失败: {e}")

    @classmethod
    def pack_cache_files(cls):
        """打包所有缓存文件

        将.npmask文件打包并用lz4压缩, 生成cached_masks.tar.lz4
        """
        try:
            if not PerformanceConfig.fill_mask_cache_dir.exists():
                return

            print(
                "    (cache) MaskCacheManager.pack_cache_files: 正在打包填充蒙版预计算缓存..."
            )
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
            print(
                f"    (cache) MaskCacheManager.pack_cache_files: 填充蒙版预计算缓存已打包至: {PerformanceConfig.fill_mask_cache_archive}"
            )

        except Exception as e:
            print(f"    (err) 打包缓存文件失败: {e}")

    @classmethod
    def extract_cache_archive(cls):
        """解压缓存文件

        解压cached_masks.tar.lz4到临时缓存目录
        """
        try:
            if not PerformanceConfig.fill_mask_cache_archive.exists():
                return

            print(
                "    (cache) MaskCacheManager.extract_cache_archive: 正在解压填充蒙版预计算缓存 cached_masks.tar.lz4"
            )
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
            print(
                "    (cache) MaskCacheManager.extract_cache_archive: 填充蒙版预计算缓存解压完成"
            )

        except Exception as e:
            print(f"    (err) 解压缓存文件失败: {e}")
