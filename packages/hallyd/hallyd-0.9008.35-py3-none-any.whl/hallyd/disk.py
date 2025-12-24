#  SPDX-FileCopyrightText: © 2021 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
"""
Management of discs, partitions and other block devices.
"""
import contextlib
import itertools
import json
import math
import os
import re
import subprocess
import time
import typing as t

import hallyd.cleanup as _cleanup
import hallyd.fs as _fs
import hallyd.lang as _lang
import hallyd.subprocess as _subprocess


@_lang.with_friendly_repr_implementation()
class Disk:

    def __init__(self, dev_path: _fs.Path):
        self.__path = dev_path

    @property
    def size_bytes(self) -> int:
        return self.__lsblk()["size"]

    @property
    def is_removable(self) -> bool:
        return self.__lsblk()["rm"]

    @property
    def is_disk(self) -> bool:
        return self.__lsblk()["type"] == "disk"

    @property
    def stable_path(self) -> str | None:
        id_path = self.__id_path()
        if id_path:
            return f"/dev/disk/by-path/{id_path}"

    @property
    def path(self) -> _fs.Path:
        return self.__path

    @property
    def partitions(self) -> list["Partition"]:
        result = []
        for partition_data in self.__lsblk().get("children", ()):
            if partition_data["type"] == "part":
                result.append(self.partition(partition_tuple(partition_data["name"])[1]))
        return result

    def __id_path(self) -> str | None:
        return self.__udev_property("ID_PATH")

    def partition_path(self, part_no: int) -> _fs.Path:
        return partition_path(self.path, part_no)

    def partition(self, part_no: int) -> "Partition":
        return Partition(self.partition_path(part_no))

    def stable_udev_filter(self) -> str:
        id_path = self.__id_path()
        if id_path:
            return f'ENV{{ID_PATH}}=="{id_path}"'
        else:
            return f"ENV{{DEVNAME}}==\"{self.__udev_property('DEVNAME')}\""

    def __lsblk(self) -> dict[str, t.Any]:
        return _lsblk(self.__path)["blockdevices"][0]

    def __udev_property(self, name: str) -> str | None:
        for line in subprocess.check_output(("udevadm", "info", self.__path, "--query=property")).decode().split("\n"):
            if line.startswith(f"{name}="):
                return line[len(name) + 1 :]

    def _has_path(self, path: str) -> bool:
        return os.path.realpath(path) == os.path.realpath(self.path)

    def __eq__(self, other):
        return isinstance(other, Disk) and (other.stable_path or other.path) == (self.stable_path or self.path)

    def __hash__(self):
        return hash(self.stable_path or self.path)


@_lang.with_friendly_repr_implementation()
class DiskSetup:

    def __init__(
        self,
        *partitions: "PartitionSetup",
        identify_by: t.Iterable[str],
        do_repartition: bool = True,
        partition_table_type: str = "gpt",
        name: str | None = None,
    ):
        """
        :param path: The path to the disk device file.
        :param repartition: If to write a new partition table (or reuse the existing one).
        """
        self.partitions = list(partitions)
        self.identify_by = identify_by
        self.do_repartition = do_repartition
        self.partition_table_type = partition_table_type
        self.name = name


@_lang.with_friendly_repr_implementation()
class _PartitionSetup:
    """
    Base class for all kinds of partitions.
    """

    def __init__(
        self,
        *,
        fs_type: "_PartitionType | None" = None,
        mountpoint: str | None = None,
        label: str | None = None,
        do_format: bool = True,
    ):
        """
        :param fs_type: The filesystem type name.
        :param mountpoint: The mountpoint to use .
        :param label: The partition label to assign.
        :param do_format: If to format the partition (or leaving it with its existing data).
        """
        self.fs_type = fs_type
        self.mountpoint = mountpoint
        self.label = label
        self.do_format = do_format

    def mountpoint_spec(self, partition: "Partition") -> "Mountpoint | None":
        if self.mountpoint:
            return Mountpoint(partition, self.mountpoint, self.fs_type)

    def make_filesystem(self, partition_dev_path: "_fs.TInputPath") -> None:
        return self.fs_type.make_filesystem(partition_dev_path)


class PartitionSizingEvent:

    def __init__(self, disk_size: int):
        self.__disk_size = disk_size

    @property
    def disk_size(self) -> int:
        return self.__disk_size


TPartitionSetupSize = int | t.Callable[[PartitionSizingEvent], int] | None


class PartitionSetup(_PartitionSetup):

    def __init__(
        self,
        *,
        index: int | None = None,
        fs_type: "_PartitionType | None" = None,
        mountpoint: str | None = None,
        label: str | None = None,
        do_format: bool = True,
        use_in_raid: str | None = None,
        size: TPartitionSetupSize = None,
        start_at_mb: float | None = None,
        flag_bootable: bool = False,
    ):
        """
        :param index: Partition index (counted from 1). Only needed in exotic cases.
        :param use_in_raid: Name of the raid to use this partition for.
                            See also the raid_name parameter of RaidPartitionSetup.__init__.
        :param size: The size in bytes.
        :param start_at_mb: The start offset in units of 1024^2 bytes.
        :param flag_bootable: If to flag this partition as bootable.
        """
        super().__init__(fs_type=fs_type, mountpoint=mountpoint, label=label, do_format=do_format)
        self.index = index
        self.use_in_raid = use_in_raid
        self.size = size
        self.start_at_mb = start_at_mb
        self.flag_bootable = flag_bootable


class RaidPartitionSetup(_PartitionSetup):

    def __init__(
        self,
        raid_name: str,
        *,
        fs_type: "_PartitionType | None" = None,
        mountpoint: str | None = None,
        label: str | None = None,
        do_format: bool = True,
        do_create_raid: bool = True,
    ):
        """
        :param raid_name: The raid to use for this partition. See also the use_in_raid parameter of Partition.__init__.
        """
        super().__init__(fs_type=fs_type, mountpoint=mountpoint, label=label, do_format=do_format)
        self.raid_name = raid_name
        self.do_create_raid = do_create_raid


@_lang.with_friendly_repr_implementation()
class Partition:

    def __init__(self, path: _fs.Path):
        self.__path = path

    @staticmethod
    def by_uuid(uuid_: str) -> "Partition":
        return Partition(_fs.Path(f"/dev/disk/by-uuid/{uuid_.lower()}"))

    @staticmethod
    def by_partuuid(uuid_: str) -> "Partition":
        return Partition(_fs.Path(f"/dev/disk/by-partuuid/{uuid_.lower()}"))

    @property
    def stable_path(self) -> _fs.Path:
        partuuid = self.partuuid
        if partuuid:
            return Partition.by_partuuid(partuuid).path

        uuid = self.uuid
        if uuid:
            return Partition.by_uuid(uuid).path

        raise IOError(f"the partition at {self.path!r} neither has a uuid nor a partuuid")

    @property
    def path(self) -> _fs.Path:
        return self.__path

    @property
    def uuid(self) -> str | None:
        try:
            return subprocess.check_output(("blkid", "-p", "-s", "UUID", "-o", "value", self.path)).decode().strip()
        except subprocess.CalledProcessError:
            return None

    @property
    def partuuid(self) -> str | None:
        try:
            return (
                subprocess.check_output(("blkid", "-p", "-s", "PART_ENTRY_UUID", "-o", "value", self.path))
                .decode()
                .strip()
            )
        except subprocess.CalledProcessError:
            return None

    @property
    def fstype(self) -> "_PartitionType | None":
        if parttype_str := _lsblk(self.path)["blockdevices"][0].get("parttype"):
            return _PartitionType.by_gpt_uuid(parttype_str)

    @property
    def disk(self) -> Disk | None:
        if pkname := _lsblk(self.path)["blockdevices"][0].get("pkname"):
            return Disk(pkname)

    @property
    def part_no(self) -> int | None:
        return _lsblk(self.path)["blockdevices"][0].get("partn")


class RaidPartition(Partition):

    def stop(self):
        subprocess.call(("mdadm", "--stop", self.path))

    @property
    def storage_devices(self) -> t.Iterable[Partition]:
        result = []

        for line in (
            subprocess.check_output(("mdadm", "--detail", "--scan", "--verbose", self.path)).decode().split("\n")
        ):
            line = line.strip()
            if line.startswith("devices="):
                for volume_dev in line[8:].split(","):
                    result.append(Partition(_fs.Path(volume_dev).resolve()))

        return result


def size(
    *,
    b: float = 0,
    kb: float = 0,
    kib: float = 0,
    mb: float = 0,
    mib: float = 0,
    gb: float = 0,
    gib: float = 0,
    tb: float = 0,
    tib: float = 0,
    pb: float = 0,
    pib: float = 0,
) -> int:
    """
    Return a size in byte for a size in prefixed units.

    :param b: The number of bytes.
    :param kb: The number of kilobytes.
    :param kib: The number of kibibytes.
    :param mb: The number of megabytes.
    :param mib: The number of mebibytes.
    :param gb: The number of gigabytes.
    :param gib: The number of gibibytes.
    :param tb: The number of terabytes.
    :param tib: The number of tebibytes.
    :param pb: The number of petabytes.
    :param pib: The number of pebibytes.
    """
    result = b
    result += kb * (1000**1)
    result += kib * (1024**1)
    result += mb * (1000**2)
    result += mib * (1024**2)
    result += gb * (1000**3)
    result += gib * (1024**3)
    result += tb * (1000**4)
    result += tib * (1024**4)
    result += pb * (1000**5)
    result += pib * (1024**5)
    return math.ceil(result)


def host_disks() -> list[Disk]:
    resset = set()
    for bk in _lsblk("--all")["blockdevices"]:
        if bk["size"] > 0:
            resset.add(_fs.Path(Disk(_fs.Path(bk["name"])).stable_path or bk["name"]))
    res = [Disk(dev_path) for dev_path in resset]
    res.sort(key=_disks_sort_key)
    return res


def host_raid_partitions() -> list[RaidPartition]:
    return [RaidPartition(f) for f in _fs.Path("/dev").glob("md*") if f.is_block_device()]


def host_partition_for_fs_path(fs_path: _fs.TInputPath) -> Partition:
    partition_dev_path = _fs.Path(subprocess.check_output(("df", "--output=source", fs_path)).decode().split("\n")[1])
    result = Partition(partition_dev_path)

    for host_disk in host_disks():
        for partition in host_disk.partitions:
            if partition.stable_path == result.stable_path:
                return partition

    return result


def partition_path(disk_path: _fs.Path, part_no: int) -> _fs.Path:
    """
    Returns a partition device path for a given disk device path and a partition number.
    Examples:

    - "/dev/sda", 1 -> "/dev/sda1"
    - "/dev/loop2", 1 -> "/dev/loop2p1"
    """
    if str(disk_path).startswith("/dev/disk/by-"):
        sep = "-part"
    elif disk_path.name[-1].isnumeric():
        sep = "p"
    else:
        sep = ""
    return _fs.Path(f"{disk_path}{sep}{part_no}")


def partition_tuple(partition_dev: _fs.TInputPath) -> tuple[_fs.Path, int]:
    """
    Returns the disk device path partition number for a given partition device path.
    Examples:

    - "/dev/sda1" -> "/dev/sda", 1
    - "/dev/loop2p1" -> "/dev/loop2", 1
    """
    partition_dev = _fs.Path(partition_dev)
    if str(partition_dev).startswith("/dev/disk/by-"):
        sep = "-part"
    else:
        sep = "p"
    a, b, c = str(partition_dev).rpartition(sep)
    if not a:
        match = re.fullmatch("^(.*\\D)(\\d+)$", c)
        if not match:
            raise ValueError(f"unexpected partition device: {partition_dev}")
        disk_dev = _fs.Path(match.group(1))
        part_no = int(match.group(2))
    else:
        disk_dev = _fs.Path(a + b)
        if not disk_dev.exists():
            disk_dev = _fs.Path(a)
        if not disk_dev.exists():
            raise ValueError(f"unable to find the disk device for partition device: {partition_dev}")
        part_no = int(c)
    return disk_dev, part_no


@_lang.with_friendly_repr_implementation()
class _PartitionType:

    def __init__(
        self,
        gpt_uuid: str,
        mbr_id: str | None = None,
        mkfs_command: list[str] | None = None,
        fstab_type_name: str | None = None,
        options: dict | None = None,
    ):
        self.__gpt_uuid = gpt_uuid
        self.__mbr_id = mbr_id
        self.__mkfs_command = mkfs_command
        self.__fstab_type_name = fstab_type_name
        self.__options = options

    def __to_json_dict__(self):
        for partition_type_name, partition_type in PartitionTypes.__dict__.items():
            if partition_type == self:
                return dict(name=partition_type_name)

    def __eq__(self, other):
        return isinstance(other, _PartitionType) and other.gpt_uuid == self.gpt_uuid and other.options == self.options

    def __hash__(self):
        return hash(self.__gpt_uuid)

    @classmethod
    def __from_json_dict__(cls, json_dict):
        return getattr(PartitionTypes, json_dict["name"])

    @property
    def gpt_uuid(self):
        return self.__gpt_uuid

    @property
    def mbr_id(self):
        return self.__mbr_id

    @property
    def options(self):
        return self.__options

    @property
    def fstab_type_name(self):
        return self.__fstab_type_name

    def make_filesystem(self, partition_path: _fs.TInputPath):
        if self.__mkfs_command:
            _subprocess.verify_tool_available(self.__mkfs_command[0])
            for _ in range(4):  # wait until definitely available
                time.sleep(2)
                for __ in range(60):
                    if os.path.exists(partition_path):
                        break
                    time.sleep(1)
            subprocess.check_call(list(map(lambda s: (partition_path if s is ... else s), self.__mkfs_command)))

    @staticmethod
    def by_gpt_uuid(parttype_uuid: str) -> "_PartitionType | None":
        for part_type in PartitionTypes.__dict__.values():
            if isinstance(part_type, _PartitionType) and part_type.gpt_uuid.upper() == parttype_uuid.upper():
                return part_type


class PartitionTypes:

    UNUSED = _PartitionType(gpt_uuid="00000000-0000-0000-0000-000000000000", mbr_id="0")

    EFI = _PartitionType(
        gpt_uuid="C12A7328-F81F-11D2-BA4B-00A0C93EC93B",
        mbr_id="0c",
        mkfs_command=["mkfs.fat", "-F32", ...],
        fstab_type_name="vfat",
    )

    EXT4 = _PartitionType(
        gpt_uuid="0FC63DAF-8483-4772-8E79-3D69D8477DE4",
        mbr_id="83",
        mkfs_command=["mkfs.ext4", "-F", ...],
        fstab_type_name="ext4",
    )

    SWAP = _PartitionType(gpt_uuid="0657FD6D-A4AB-43C4-84E5-0933C84B4F4F", mbr_id="82", mkfs_command=["mkswap", ...])

    ENCRYPTED_SWAP = _PartitionType(
        gpt_uuid="0657FD6D-A4AB-43C4-84E5-0933C84B4F4F",
        mbr_id="82",
        mkfs_command=["mkswap", ...],
        options={"encrypted": True},
    )

    RAID = _PartitionType(gpt_uuid="A19D880F-05FC-4D3B-A006-743F0F84911E", mbr_id="fd")


@_lang.with_friendly_repr_implementation()
class RaidSetup:

    def __init__(self, name: str, partitions: list[_fs.Path]):
        self.name = name
        self.partitions = partitions

    @_lang.with_retry(interval=3)
    def create(self, *, do_create: bool = True) -> RaidPartition:
        dev_path = _fs.Path("/dev/md/")(self.name[:32])
        if do_create:
            subprocess.check_call(
                [
                    "mdadm",
                    "--create",
                    dev_path,
                    "--level=1",
                    "--run",
                    f"--raid-devices={len(self.partitions)}",
                    *self.partitions,
                ]
            )
        return RaidPartition(dev_path)


@_lang.with_friendly_repr_implementation()
class OrderedPartitionSetupsEntry:

    def __init__(self, part_no: int, partition_setup: PartitionSetup):
        self.__part_no = part_no
        self.__partition_setup = partition_setup

    @property
    def part_no(self) -> int:
        return self.__part_no

    @property
    def partition_setup(self) -> PartitionSetup | None:
        return self.__partition_setup


def effective_partition_setup_order(partition_setups: list[PartitionSetup]) -> list[OrderedPartitionSetupsEntry]:
    raw_result = []
    indexed_partitions = []
    for partition_setup in partition_setups:
        if partition_setup.index is None:
            raw_result.append(partition_setup)
        else:
            indexed_partitions.append(partition_setup)
    indexed_partitions.sort(key=lambda prt: prt.index)
    for indexed_partition in indexed_partitions:
        while len(raw_result) < indexed_partition.index:
            raw_result.append(None)
        raw_result.insert(indexed_partition.index - 1, indexed_partition)
    return [
        OrderedPartitionSetupsEntry(i_partition_setup + 1, partition_setup)
        for i_partition_setup, partition_setup in enumerate(raw_result)
    ]


def raid_setups_from_disk_intents(disk_intents: list["DiskIntent"]) -> dict[str, RaidSetup]:
    result = {}
    for disk_intent in disk_intents:
        for partition_entry in effective_partition_setup_order(disk_intent.setup.partitions):
            if partition_entry.partition_setup.use_in_raid:
                partitionpath = partition_path(disk_intent.disk.path, partition_entry.part_no)
                raid_setup = result.get(partition_entry.partition_setup.use_in_raid)
                if not raid_setup:
                    raid_setup = RaidSetup(partition_entry.partition_setup.use_in_raid, [])
                    result[partition_entry.partition_setup.use_in_raid] = raid_setup
                raid_setup.partitions.append(partitionpath)
    return result


@contextlib.contextmanager
def connect_diskimage(disk_image_path: "_fs.Path") -> t.ContextManager["_fs.Path"]:
    subprocess.check_output(("modprobe", "loop"))
    idev = 0
    while True:
        loop_dev_path = _fs.Path(f"/dev/loop{idev}")
        if not loop_dev_path.exists():
            break
        if subprocess.call(("losetup", "-P", loop_dev_path, disk_image_path)) == 0:
            cleanup = _cleanup.add_cleanup_task(
                _detach_loop_device, loop_dev_path, loop_device_by_dev_path(loop_dev_path).back_file
            )
            try:
                yield loop_dev_path
            finally:
                cleanup()
                while True:
                    if not subprocess.check_output(("losetup", "--associated", disk_image_path)).strip():
                        break
                    time.sleep(0.1)
            return
        idev += 1
    raise IOError("no free loop device available")


@contextlib.contextmanager
def connect_diskimage_buffered(dev_path: "_fs.Path", *, buffer_size_gb: float) -> t.ContextManager["_fs.Path"]:
    with _fs.temp_dir() as temp_dir:
        buffer_image_path = temp_dir("image")
        create_diskimage(buffer_image_path, size_gb=buffer_size_gb)
        try:
            with connect_diskimage(buffer_image_path) as buffer_device_path:
                yield buffer_device_path
            subprocess.check_output(("dd", f"if={buffer_image_path}", f"of={dev_path}", "bs=1M"))
        finally:
            buffer_image_path.unlink()


def create_diskimage(path: "str | _fs.Path", *, size_gb: float) -> None:
    subprocess.check_output(("dd", "if=/dev/zero", f"of={path}", "bs=1", "count=0", f"seek={int(size_gb*1024**3)}"))


def all_loop_devices():
    # noinspection SpellCheckingInspection
    return [LoopDevice(**kwargs) for kwargs in json.loads(subprocess.check_output(("losetup", "-Jl")))["loopdevices"]]


def loop_device_by_dev_path(dev_path: "_fs.Path") -> "LoopDevice | None":
    for loop_device in all_loop_devices():
        if loop_device.dev_path == dev_path:
            return loop_device


class LoopDevice:

    def __init__(self, **kwargs):
        self.__dev_path = _fs.Path(kwargs["name"])
        self.__back_file = _fs.Path(kwargs["back-file"])

    @property
    def dev_path(self) -> "_fs.Path":
        return self.__dev_path

    @property
    def back_file(self) -> "_fs.Path":
        return self.__back_file

    def detach(self):
        subprocess.check_output(("losetup", "-d", self.dev_path), stderr=subprocess.STDOUT)


@_lang.with_friendly_repr_implementation()
class Mountpoint:

    def __init__(self, partition: Partition, mountpoint: str, fstype: "_PartitionType"):
        self.partition = partition
        self.mountpoint = mountpoint
        self.fstype = fstype

    def fstab_line(self) -> str:
        fstab_type = self.fstype.fstab_type_name
        fstab_opts_dict = {"errors": "remount-ro"}
        if self.fstype == PartitionTypes.EFI:
            fstab_opts_dict["umask"] = "0077"
        fstab_opts = ",".join([f"{k}={v}" for k, v in fstab_opts_dict.items()])
        fstab_pass = "1" if (self.mountpoint == "/") else "2"
        if not self.partition.uuid:
            raise IOError("the partition does not have a uuid")
        return f"\nUUID={self.partition.uuid} {self.mountpoint} {fstab_type} {fstab_opts} 0 {fstab_pass}\n"

    def mount(self, *, prefix: str | None = None, create_before: bool = True):
        mountpoint = _fs.Path((f"{prefix}/" if prefix else "") + self.mountpoint)
        if create_before:
            os.makedirs(mountpoint, exist_ok=True)
        mount(self.partition.path, mountpoint)

    def umount(self):
        umount(self.partition.path)


@_lang.with_retry(interval=30, tries=250, retry_on=(subprocess.CalledProcessError,))
# retry must be so aggressive due to unmount issues on multiple parallel bind-mounted /dev/pts
def umount(path: _fs.Path):
    if not os.path.ismount(path):
        return
    subprocess.check_call(("umount", path))


def mount(dev_path: _fs.Path, target_path: _fs.Path):
    subprocess.check_call(("mount", dev_path, target_path))


@_lang.with_friendly_repr_implementation()
class DiskIntent:

    def __init__(self, disk: Disk, setup: DiskSetup):
        self.__disk = disk
        self.__setup = setup

    @property
    def disk(self):
        return self.__disk

    @property
    def setup(self):
        return self.__setup

    def udev_rule_for_alias(self) -> str:
        if not self.setup.name:
            return ""
        disk_filter = self.disk.stable_udev_filter()
        pprefix = "p" if self.setup.name[-1].isdecimal() else ""
        return (
            f'{disk_filter}, ENV{{DEVTYPE}}=="disk", SYMLINK+="{self.setup.name}"\n'
            f'{disk_filter}, ENV{{DEVTYPE}}=="partition", SYMLINK+="{self.setup.name}{pprefix}%n"\n'
        )

    def repartition(self) -> None:
        if not self.setup.do_repartition:
            return
        if self.setup.partition_table_type == "mbr":
            partition_spec_label = "dos"
            partition_type_id_attr = "mbr_id"
        elif self.setup.partition_table_type == "gpt":
            partition_spec_label = "gpt"
            partition_type_id_attr = "gpt_uuid"
        else:
            raise ValueError(f"partition_table_type unsupported: {self.setup.partition_table_type}")
        repartition_specs = f"label:{partition_spec_label}\n\n"
        asterisk_part_size = self.disk.size_bytes - size(mib=3)
        asterisk_parts = 0
        partition_sizes = {
            partition: (
                partition.size(PartitionSizingEvent(self.disk.size_bytes))
                if callable(partition.size)
                else partition.size
            )
            for partition in self.setup.partitions
        }

        for partition in self.setup.partitions:
            if partition_sizes[partition] is None:
                asterisk_parts += 1
            else:
                asterisk_part_size -= partition_sizes[partition]
        for _inp, partition in enumerate(self.setup.partitions):
            partition_size = partition_sizes[partition]
            if partition_size is None:
                partition_size = int(asterisk_part_size / asterisk_parts)
            partition_type = PartitionTypes.RAID if partition.use_in_raid else partition.fs_type
            partition_type_id = getattr(partition_type, partition_type_id_attr)
            if partition.fs_type == "efi" and partition_sizes[partition] < size(mib=32):
                raise ValueError("efi partition must be at least 32MiB in size")
            label_str = f', name="{partition.label}"' if partition.label else ""
            repartition_specs += f"size={math.ceil(partition_size/size(mib=1))}MiB, type={partition_type_id}{label_str}"
            if partition.start_at_mb:
                repartition_specs += f", start={int(partition.start_at_mb)}MiB"
            if partition.flag_bootable:
                repartition_specs += ", bootable"
            repartition_specs += "\n"
        self.__write_partition_table(repartition_specs)
        self.__reread_partition_table()

    @_lang.with_retry(interval=3)
    def __write_partition_table(self, repartition_specs):
        _subprocess.check_call_with_stdin_string(("sfdisk", self.disk.path), stdin=repartition_specs)

    @_lang.with_retry(interval=3)
    def __reread_partition_table(self):
        subprocess.check_call(("blockdev", "--rereadpt", self.disk.path))


def combine_disks_to_setups(disks: list[Disk], disk_setups: list[DiskSetup]) -> list[DiskIntent]:
    result = []
    for disk_setup, disk in find_disks_for_setups(disks, disk_setups).items():
        result.append(DiskIntent(disk, disk_setup))
    return result


def find_disks_for_setups(disks: list[Disk], disk_setups: list[DiskSetup]) -> dict[DiskSetup, Disk]:
    result = {}
    disks = list(sorted(disks, key=_disks_sort_key))

    for disk_setups_ in itertools.permutations(disk_setups):
        try:
            for disk_setup in disk_setups_:
                disk = _find_disk_for_setup(disks, disk_setup)
                disks.remove(disk)
                result[disk_setup] = disk
            return result
        except Exception:  # TODO only if no device found
            pass

    raise IOError("unable to find disks for all the given disk setups")


def find_partition_for_setup(disk: Disk, disk_setup: DiskSetup, partition: PartitionSetup) -> Partition:
    ordered_partitions = [x.partition_setup for x in effective_partition_setup_order(disk_setup.partitions)]
    partition_idx = ordered_partitions.index(partition)
    return disk.partition(partition_idx + 1)


def reload_devices():
    subprocess.check_call(("udevadm", "trigger", "--action=change"))  # otherwise no /dev/disk/by-uuid/... for nbd


# noinspection PyPep8Naming
def EfiPartitionSetup(**kwargs):
    return PartitionSetup(size=size(mib=521), **{"fs_type": PartitionTypes.EFI, "mountpoint": "/boot/efi", **kwargs})


# noinspection PyPep8Naming
def NotEfiPartitionSetup():
    return EfiPartitionSetup(fs_type=PartitionTypes.UNUSED, mountpoint=None)


def enable_swap(partition_dev: _fs.TInputPath, try_enable_instantly: bool = True) -> None:
    partition = Partition(_fs.Path(partition_dev))
    partition_dev = partition.stable_path

    if partition.fstype != PartitionTypes.ENCRYPTED_SWAP:
        if not partition.disk:
            raise RuntimeError("bad partition type")

        subprocess.call(
            ("sfdisk", "--part-type", partition.disk.path, partition.part_no, PartitionTypes.ENCRYPTED_SWAP.gpt_uuid)
        )

    existing_entries = set()
    for crypttab_line in _fs.Path("/etc/crypttab").read_text().split("\n"):
        if len(crypttab_line_parts := crypttab_line.split()) == 4:
            if crypttab_line_parts[1] == str(partition_dev):
                return
            existing_entries.add(crypttab_line_parts[0])

    i_swap = 0
    while (swap_name := f"krz_swap{i_swap}") in existing_entries:
        i_swap += 1

    _fs.Path("/etc/crypttab").append_data(f"{swap_name}    {partition_dev}    /dev/urandom    swap")
    _fs.Path("/etc/fstab").append_data(f"/dev/mapper/{swap_name}    none    swap    defaults    0    0")

    if try_enable_instantly:
        subprocess.check_call(("systemctl", "daemon-reload"))
        subprocess.check_call(("systemctl", "start", "swap.target"))


def _lsblk(*params) -> dict[str, t.Any]:
    _subprocess.verify_tool_available("lsblk")
    return json.loads(subprocess.check_output(("lsblk", "--json", "--paths", "--bytes", "--output-all", *params)))


def _disks_sort_key(disk: Disk):
    path = disk.stable_path or f"~{disk.path}"
    return path.replace("-", ".").replace("-", ".").split(".")


def _find_disk_for_setup(disks: list[Disk], disk_setup: DiskSetup) -> Disk:
    for disk in disks:
        conditions_met = True
        for identify_by_condition in disk_setup.identify_by:
            eval_scope = {k: getattr(disk, k) for k in {**disk.__dict__, **type(disk).__dict__}.keys()}
            if not eval(identify_by_condition, eval_scope, eval_scope):
                conditions_met = False
                break
        if conditions_met:
            return disk
    raise IOError(f"no device found for {disk_setup}")


def _detach_loop_device(dev_path, back_file):
    loop_device = loop_device_by_dev_path(dev_path)
    if loop_device and loop_device.back_file == back_file:
        loop_device.detach()
