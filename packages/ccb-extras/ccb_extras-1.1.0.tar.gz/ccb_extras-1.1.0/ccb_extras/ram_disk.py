"""RAM disk utilities for macOS."""

import argparse
import atexit
import logging
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from tempfile import mktemp
from time import sleep

from ccb_essentials.os import is_sudo
from ccb_essentials.subprocess import subprocess_command
from humanfriendly import InvalidSize, parse_size


log = logging.getLogger(__name__)

BLOCKS_PER_MB = 2048  # https://gist.github.com/htr3n/344f06ba2bb20b1056d7d5570fe7f596
CHMOD = '/bin/chmod'
DISKUTIL = '/usr/sbin/diskutil'
HDIUTIL = '/usr/bin/hdiutil'
SUDO = '/usr/bin/sudo'
VOLUMES = Path('/Volumes')


def mount_ram_disk(
    size: int | str,
    path: Path | str | None = None,
    unmount_at_exit: bool = False,
) -> Path | None:
    """Create a RAM disk. Filesystem is HFS+ (Mac OS Extended)."""
    if type(size) is int:
        size_bytes = size
    elif type(size) is str:
        try:
            size_bytes = parse_size(size)
        except InvalidSize as e:
            log.warning(e)
            return None

    if path is None:
        rd = Path(mktemp(dir=VOLUMES, prefix='RAM_Disk_'))
    else:
        rd = path if type(path) is Path else Path(path)
        assert rd.parent == VOLUMES
    if rd.exists():
        log.warning('RAM disk path exists: %s', rd)
        return None

    log.debug('mount_ram_disk(%d, %s)', size_bytes, rd)

    blocks = int(size_bytes / 1024 / 1024 * BLOCKS_PER_MB)
    cmd = f"{HDIUTIL} attach -owners on -nomount ram://{blocks}"
    log.debug(cmd)
    device = subprocess_command(cmd)
    if device is None:
        return None
    device = device.strip()
    cmd = f"{DISKUTIL} erasevolume HFS+ {rd.name} {device} "
    if is_sudo():
        cmd += f" && {SUDO} {DISKUTIL} enableOwnership {rd}"
        cmd += f" && {SUDO} {CHMOD} o+w {rd}"
    log.debug(cmd)
    if subprocess_command(cmd) is None:
        return None

    if unmount_at_exit:
        atexit.register(unmount_ram_disk, rd)

    return rd


def unmount_ram_disk(path: Path | str) -> bool:
    """Destroy a RAM disk."""
    log.debug('unmount_ram_disk(%s)', path)
    cmd = f"{HDIUTIL} detach {path}"
    log.debug(cmd)
    return subprocess_command(cmd) is not None


@contextmanager
def ram_disk(
    size: int | str,
    path: Path | str | None = None,
) -> Generator[Path | None]:
    """Create and then clean up a temporary RAM disk."""
    rd = mount_ram_disk(size, path=path, unmount_at_exit=False)
    if rd is None:
        yield None
        return
    try:
        yield rd
    finally:
        unmount_ram_disk(rd)


# todo tests
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=str, default="1GB", help="size of RAM disk to create (human readable)")
    args = parser.parse_args()

    disk1 = mount_ram_disk(args.size, unmount_at_exit=False)
    assert disk1
    print(disk1, disk1.exists())
    sleep(2)
    print('unmount 1: ', unmount_ram_disk(disk1))
    print('unmount 2: ', unmount_ram_disk(disk1))  # Expect an error on the second attempt

    print()
    sleep(2)
    disk2 = mount_ram_disk(args.size, unmount_at_exit=True)
    assert disk2
    print(disk2, disk2.exists())  # Persists to end of process

    print()
    sleep(2)
    with ram_disk(args.size) as disk3:
        assert disk3
        print(disk3, disk3.exists())  # True
        sleep(2)
        print(disk3, disk3.exists())  # True
    print(disk3, disk3.exists())  # False
