# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
import platform
import sys
import sysconfig

from core_platform import ArchitectureType
from core_platform.platform_dtos import PlatformInfo
from core_platform.platform_types import PlatformType, SystemType

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["get_platform_info", "get_architecture_type", "get_platform"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def get_platform_info() -> PlatformInfo:
    system = platform.system().lower()
    machine = platform.machine().lower()
    is_64bit = sys.maxsize > 2**32
    return PlatformInfo(system=system, machine=machine, is_64bit=is_64bit)


def get_architecture_type() -> PlatformType:
    info: PlatformInfo = get_platform_info()
    if info.system == SystemType.LINUX:
        if info.is_64bit and info.machine == ArchitectureType.INTEL_64:
            return PlatformType.LINUX_x86_64
    elif info.system == SystemType.WIN:
        if info.machine == ArchitectureType.AMD_64:
            return PlatformType.WIN_64
    elif info.system == SystemType.MACOSX:
        if info.machine in [ArchitectureType.INTEL_64, ArchitectureType.APPLE_64]:
            return PlatformType.MACOSX_10_9_x86_64
    raise ValueError(f"Unknown architecture of {info}")


def get_platform() -> str:
    """Return a string with current platform (system and machine architecture).

    This attempts to improve upon `sysconfig.get_platform` by fixing some
    issues when running a Python interpreter with a different architecture than
    that of the system (e.g. 32bit on 64bit system, or a multiarch build),
    which should return the machine architecture of the currently running
    interpreter rather than that of the system (which didn't seem to work
    properly). The reported machine architectures follow platform-specific
    naming conventions (e.g. "x86_64" on Linux, but "x64" on Windows).

    Example output strings for common platforms:

        darwin_(ppc|ppc64|i368|x86_64|arm64)
        linux_(i686|x86_64|armv7l|aarch64)
        windows_(x86|x64|arm32|arm64)

    """

    info: PlatformInfo = get_platform_info()
    platform_machine = sysconfig.get_platform().split("-")[-1].lower()

    if info.system == SystemType.LINUX:  # fix running 32bit interpreter on 64bit system
        if not info.is_64bit and platform_machine == ArchitectureType.INTEL_64:
            platform_machine = ArchitectureType.INTEL_32.value
        elif not info.is_64bit and platform_machine == ArchitectureType.ARM_64:
            platform_machine = ArchitectureType.ARM_32.value

    elif info.system == SystemType.WIN:  # return more precise machine architecture names
        if platform_machine == ArchitectureType.AMD_64:
            platform_machine = ArchitectureType.CPU_64.value
        elif platform_machine == ArchitectureType.WIN_32:
            platform_machine = info.machine if info.is_64bit else ArchitectureType.CPU_32.value

    elif info.system == SystemType.MACOSX:  # get machine architecture of multi-architecture binaries
        if any(x in platform_machine for x in ("fat", "intel", "universal")):
            platform_machine = info.machine

    # some more fixes based on examples in https://en.wikipedia.org/wiki/Uname
    if not info.is_64bit and platform_machine in (ArchitectureType.INTEL_64, ArchitectureType.AMD_64):
        if any(x in info.system for x in ("cygwin", "mingw", "msys")):
            platform_machine = ArchitectureType.INTEL_32.value
        else:
            platform_machine = ArchitectureType.INTEL_OLD_32.value

    return f"{info.system}_{platform_machine}"
