import logging
import os
import weakref
from tempfile import TemporaryDirectory


class TemporaryFileSystem:
    """
    Temporary directory utils class
    used for data manipulators
    """

    def __init__(self, file_format: str = "csv") -> None:
        self.file_format = file_format
        self._tmp_dir = TemporaryDirectory()
        self._last_path: str
        self._finalizer = weakref.finalize(self, self._safe_cleanup, self._tmp_dir.name)

    def __del__(self) -> None:
        """Fallback cleanup (not guaranteed but added as safety net)."""
        self.cleanup()

    @staticmethod
    def _safe_cleanup(dir_path: str) -> None:
        """Safely remove directory ignoring some errors."""
        try:
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path, topdown=False):
                    for name in files:
                        os.unlink(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(dir_path)
        except (OSError, PermissionError):
            pass

    def cleanup(self) -> None:
        """Explicit cleanup method. Safe to call multiple times."""
        if hasattr(self, "_finalizer") and self._finalizer.alive:
            self._finalizer()

    @property
    def tmp_dir(self) -> str:
        return self._tmp_dir.name

    @property
    def files(self) -> list:
        return os.listdir(str(self.tmp_dir))

    @property
    def next_filename(self) -> str:
        number = 0
        avaliable = [int(x.split(".")[0].split("_")[-1]) for x in self.files]
        if len(avaliable) != 0:
            number = max(avaliable) + 1
        return f"data_{number}.{self.file_format}"

    def save_path(self) -> str:
        self._last_path = os.path.join(str(self.tmp_dir), self.next_filename)
        return self._last_path

    @property
    def dir_info(self) -> None:
        """
        Shows temporary directory info
        file - file size in mb
        """
        for file in self.files:
            check_file = os.path.join(self.tmp_dir, file)
            size = os.path.getsize(check_file) / 1024**2
            print(f"{check_file}: {size} mb")
