# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from enum import Enum

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["SystemType", "ArchitectureType", "PlatformType"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class SystemType(str, Enum):
    LINUX = "linux"
    WIN = "windows"
    MACOSX = "darwin"


class ArchitectureType(str, Enum):
    INTEL_OLD_32 = "i386"
    INTEL_32 = "i686"
    INTEL_64 = "x86_64"
    ARM_32 = "armv7l"
    ARM_64 = "aarch64"
    AMD_64 = "amd64"
    APPLE_64 = "arm64"
    WIN_32 = "win32"
    CPU_32 = "x86"
    CPU_64 = "x64"


class PlatformType(str, Enum):
    LINUX_x86_64 = "linux_x86_64"
    WIN_64 = "win_amd64"
    MACOSX_10_9_x86_64 = "macosx_10_9_universal2"
