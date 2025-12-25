import os
import platform
import hashlib
import requests
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

"""
功能描述
    CacheAssetDownloader 是一个智能的资源下载器，主要用于管理大型文件（如机器学习模型、数据集等）的下载和本地缓存。

跨平台缓存管理：
    Windows：使用 %LOCALAPPDATA% 或 用户目录/AppData/Local
    macOS：使用 ~/Library/Caches
    Linux/Docker：使用 $XDG_CACHE_HOME 或 ~/.cache

智能缓存机制：
    自动检查本地缓存是否存在
    支持 MD5 哈希验证确保文件完整性
    避免重复下载，节省带宽和时间

安全下载：
    流式下载，适合大文件
    异常处理和错误恢复
    文件验证失败时自动清理
"""


class CacheAssetDownloader:
    def __init__(self, asset_sub_folder: str, download_url: str, expected_hash: Optional[str] = None):
        self.asset_sub_folder = asset_sub_folder
        self.download_url = download_url
        self.expected_hash = expected_hash

        # 设置缓存目录
        self.cache_dir = self._get_cache_dir()
        self.asset_path = None

        # 自动下载资源
        self._download_if_needed()

    def _get_cache_dir(self) -> Path:
        """获取缓存目录"""
        system = platform.system().lower()

        if system == 'windows':
            base_dir = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
        elif system == 'darwin':  # macOS
            base_dir = Path.home() / 'Library' / 'Caches'
        else:  # Linux/Docker
            base_dir = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache'))

        cache_dir = base_dir / 'orbit_assets' / self.asset_sub_folder
        cache_dir.mkdir(parents=True, exist_ok=True)

        print(f"You current system: >>>{system}<<<, with cache path: >>>{cache_dir}<<<")
        return cache_dir

    def _validate_file(self, file_path: Path) -> bool:
        """验证文件"""
        if not file_path.exists():
            return False

        if not self.expected_hash:  # 如果没开启 hash 验证，则直接返回
            return True

        # 计算MD5
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        return hash_md5.hexdigest().lower() == self.expected_hash.lower()

    def _download_file(self, url: str, target_path: Path) -> bool:
        """下载文件"""
        try:
            print(f"正在下载: {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"下载完成: {target_path}")
            return True
        except Exception as e:
            print(f"下载失败: {e}")
            return False

    def _download_if_needed(self):
        """检查并下载资源"""
        # 确定文件名
        filename = os.path.basename(urlparse(self.download_url).path)
        asset_file = self.cache_dir / filename

        # 检查缓存
        if self._validate_file(asset_file):
            print(f"使用缓存文件: {asset_file}")
            self.asset_path = asset_file
            return

        # 下载文件
        if not self._download_file(self.download_url, asset_file):
            raise RuntimeError(f"下载失败: {self.download_url}")

        # 验证文件
        if not self._validate_file(asset_file):
            asset_file.unlink(missing_ok=True)
            raise RuntimeError("文件验证失败")

        self.asset_path = asset_file

    def get_path(self) -> Path:
        """获取资源路径"""
        return self.asset_path


if __name__ == "__main__":
    downloader = CacheAssetDownloader(
        asset_sub_folder="fasttext",
        download_url="https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin",
    )

    # cache_dir = downloader._get_cache_dir()
    # print(cache_dir)

    model_path = downloader.get_path()
    print(f"模型路径: {model_path}")
