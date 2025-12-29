from pathlib import Path
from sys import platform
from packaging import version
import os

class File:
    @staticmethod
    def temp_dir():
        home = str(Path.home())
        is_win = platform.startswith("win")
        if is_win:
            return "%s\\AppData\\Local\\Temp\\Robomotion" % home
        return "/tmp/robomotion"

    @staticmethod
    def dir_exists(dir_path: str) -> bool:
        """Check if a directory exists."""
        try:
            return os.path.isdir(dir_path)
        except Exception:
            return False

    @staticmethod
    def file_exists(dir_path: str, file_name: str = None) -> bool:
        """
        Check if a file exists.

        Args:
            dir_path: Directory path, or full file path if file_name is None
            file_name: Optional file name to join with dir_path

        Returns:
            True if file exists and is not a directory
        """
        try:
            if file_name:
                full_path = os.path.join(dir_path, file_name)
            else:
                full_path = dir_path
            return os.path.isfile(full_path)
        except Exception:
            return False


class Version:
    @staticmethod
    def is_version_less_than(ver: str, other: str) -> bool:
        """
        Compare two version strings.

        Args:
            ver: First version string
            other: Second version string to compare against

        Returns:
            True if ver is less than other
        """
        if not ver or ver in ("0.0", "0.0.0"):
            return True
        try:
            v = version.parse(ver)
            v2 = version.parse(other)
            return v < v2
        except Exception:
            return True


# Standalone utility functions (matching Go's utils package)

def dir_exists(dir_path: str) -> bool:
    """Check if a directory exists."""
    return File.dir_exists(dir_path)


def file_exists(dir_path: str, file_name: str = None) -> bool:
    """Check if a file exists."""
    return File.file_exists(dir_path, file_name)


def get_temp_path():
    """Get the platform-specific temp path for Robomotion."""
    if platform == "win32":
        home = os.getenv("HOMEDRIVE", "") + os.getenv("HOMEPATH", "")
        if not home:
            home = os.getenv("USERPROFILE", "")
        return os.path.join(home, "AppData", "Local", "Robomotion", "temp")
    elif platform.startswith("linux") or platform == "darwin":
        return os.path.join(user_home_dir(), ".config", "robomotion", "temp")

    return ""


def user_home_dir():
    """Get the user's home directory."""
    if platform == "win32":
        home = os.getenv("HOMEDRIVE", "") + os.getenv("HOMEPATH", "")
        if not home:
            home = os.getenv("USERPROFILE", "")
        return home
    return os.getenv("HOME", "")