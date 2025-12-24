import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from threading import RLock
from typing import Dict, Any
from .wrap import singleton

logger = logging.getLogger(__name__)


class FileStorageError(Exception):
    """Base exception for file storage operations"""
    pass


@singleton
class TempFileManager:
    def __init__(self, config: Dict[str, Any], work_dir = None):
        self.config = config
        self.service_types = config.get("SERVICE_TYPES", ['tmp'])  # 保留原有服务类型分类
        if work_dir is None:
            work_dir = os.path.curdir  # 保留原有服务类型分类
        storage_path = config.get("STORAGE_PATH", os.path.curdir)  # 保留原有服务类型分类
        self.storage_root = Path(os.path.join(work_dir, storage_path))
        self.lock = RLock()

    def _get_storage_root(self) -> Path:
        """获取已验证的存储根路径"""
        if not self.storage_root.exists():
            self.storage_root.mkdir(parents=True, exist_ok=True)
        return self.storage_root.resolve()

    def generate_file_id(self, service_type: str, ext: str, name: str = None) -> str:
        """Generate structured file ID with timestamp"""
        if service_type not in self.service_types:
            raise ValueError(f"Invalid service type: {service_type}")

        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d/%H%M")
            unique_id = uuid.uuid4().hex[:8]
            name = f"{timestamp}_{unique_id}"

        return f"{service_type}/{name}.{ext.lstrip('.')}"

    def save(self, data: bytes, service_type: str, ext: str) -> str:
        """Save temporary file with thread-safe operation"""
        with self.lock:
            try:
                file_id = self.generate_file_id(service_type, ext)
                dest_path = self._get_storage_root() / file_id
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                with open(dest_path, 'wb') as f:
                    f.write(data)

                logger.debug(f"Saved temp file: {file_id}")
                return file_id
            except Exception as e:
                logger.error(f"Save failed: {str(e)}")
                raise FileStorageError("Failed to save file") from e

    def get_path(self, file_id: str) -> Path:
        """Get full filesystem path for a file ID"""
        path = self._get_storage_root() / file_id
        # 确保父目录存在（自动创建缺失的层级）
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def delete(self, file_id: str):
        """Delete a temporary file"""
        with self.lock:
            try:
                path = self.get_path(file_id)
                path.unlink(missing_ok=True)
                logger.debug(f"Deleted temp file: {file_id}")
            except Exception as e:
                logger.error(f"Delete failed: {str(e)}")
                raise FileStorageError("Failed to delete file") from e

    def clean_expired(self):
        """Clean files older than retention period"""
        retention_hours = self.config.get('MAX_RETENTION_HOURS', 24)  # 使用新配置项
        cutoff_time = datetime.now() - timedelta(hours=retention_hours)

        with self.lock:
            for root, _, files in os.walk(self._get_storage_root(), topdown=False):
                for file in files:
                    file_path = Path(root) / file
                    # 跳过用户上传的文件（upload目录）
                    if file_path.parts[-3] == 'upload':
                        continue

                    create_time = datetime.fromtimestamp(file_path.stat().st_ctime)
                    update_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if create_time < cutoff_time or update_time < cutoff_time:
                        try:
                            file_path.unlink()
                            logger.info(f"Cleaned expired file: {file_path}")
                        except Exception as e:
                            logger.error(f"Clean expired failed: {str(e)}")
                current_dir = Path(root)
                if 'upload' not in current_dir.parts:
                    try:
                        # 判断目录是否为空（没有文件或子目录）
                        if not any(current_dir.iterdir()):
                            current_dir.rmdir()
                            logger.info(f"Removed empty directory: {current_dir}")
                    except Exception as e:
                        logger.error(f"Failed to remove directory: {current_dir}, error: {str(e)}")

    def _update_access_time(self, file_path: Path):
        """Update last access time metadata"""
        try:
            now = datetime.now().timestamp()
            os.utime(file_path, (now, now))
        except Exception as e:
            logger.warning(f"Failed to update access time for {file_path}: {str(e)}")

    def get_usage(self) -> dict:
        """Get storage usage statistics"""
        total_size = 0
        file_count = 0

        with self.lock:
            for root, _, files in os.walk(self._get_storage_root()):
                for file in files:
                    file_path = Path(root) / file
                    total_size += file_path.stat().st_size
                    file_count += 1

        return {
            'total_files': file_count,
            'total_size_gb': round(total_size / (1024 ** 3), 2),
            'max_retention_hours': self.config['MAX_RETENTION_HOURS'],
            'cleanup_interval_hours': self.config['CLEANUP_INTERVAL_HOURS'],
            'max_size_gb': self.config['MAX_SIZE_GB']
        }

    def clean_lru_files(self):
        """Clean files based on least recently used policy"""
        max_size_bytes = self.config['MAX_SIZE_GB'] * 1024 ** 3
        usage = self.get_usage()

        if usage['total_size_gb'] <= self.config['MAX_SIZE_GB']:
            return

        file_list = []
        with self.lock:
            # Collect all files with access times
            for root, _, files in os.walk(self._get_storage_root()):
                for file in files:
                    file_path = Path(root) / file
                    if 'upload' in file_path.parts:
                        continue
                    try:
                        stat = file_path.stat()
                        file_list.append((stat.st_atime, file_path, stat.st_size))
                    except Exception as e:
                        logger.error(f"Error reading {file_path}: {str(e)}")

            # Sort by access time (oldest first)
            file_list.sort()

            # Delete files until under size limit
            deleted_size = 0
            target_size = max_size_bytes - (max_size_bytes * 0.1)  # Leave 10% buffer
            deleted_files = 0
            for atime, path, size in file_list:
                if (usage['total_size_gb'] * 1024 ** 3 - deleted_size) <= target_size:
                    break
                try:
                    path.unlink()
                    deleted_size += size
                    deleted_files += 1
                    logger.info(f"LRU cleaned: {path} (last accessed: {datetime.fromtimestamp(atime)})")
                except Exception as e:
                    logger.error(f"Failed to delete {path}: {str(e)}")

        return {
            'deleted_files': deleted_files,
            'deleted_size_gb': round(deleted_size / (1024 ** 3), 2),
            'remaining_size_gb': round((usage['total_size_gb'] - deleted_size / 1024 ** 3), 2),
            'original_size_gb': usage['total_size_gb']
        }
