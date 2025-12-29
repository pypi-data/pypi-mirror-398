from .backblaze import BackblazeStorage
from .minio import MinioStorage
from .staticfiles import StaticFilesStorage

__all__ = ["MinioStorage", "BackblazeStorage", "StaticFilesStorage"]
