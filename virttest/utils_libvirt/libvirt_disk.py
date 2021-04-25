"""
libvirt disk related utility functions
"""
import logging

from avocado.core import exceptions

from virttest import utils_misc
from virttest.utils_test import libvirt

from virttest.libvirt_xml.devices.disk import Disk


def create_disk(disk_type, path=None, size="500M", disk_format="raw", extra='',
                session=None):
    """
    Create disk on local or remote

    :param disk_type: Disk type
    :param path: The path of disk
    :param size: The size of disk
    :param disk_format: The format of disk
    :param extra: Extra parameters
    :param session： Session object to a remote host or guest
    :return: The path of disk
    :raise: TestError if the disk can't be created
    """

    if session:
        if disk_type == "file":
            disk_cmd = ("qemu-img create -f %s %s %s %s"
                        % (disk_format, extra, path, size))
        else:
            # TODO: Add implementation for other types
            raise exceptions.TestError("Unknown disk type %s" % disk_type)

        status, stdout = utils_misc.cmd_status_output(disk_cmd, session=session)
        if status:
            raise exceptions.TestError("Failed to create img on remote: cmd: {} "
                                       "status: {}, stdout: {}"
                                       .format(disk_cmd, status, stdout))
        return path
    else:
        return libvirt.create_local_disk(disk_type, path=path, size=size,
                                         disk_format=disk_format, extra=extra)


def create_primitive_disk_xml(type_name, disk_device, device_target, device_bus,
                              device_format, disk_src_dict, disk_auth_dict):
    """
    Creates primitive disk xml

    :param type_name: disk type
    :param disk_device: disk device
    :param device_target: target device
    :param device_bus: device bus
    :param device_format: device format
    :param disk_src_dict: disk source, dict format like below
           disk_src_dict = {"attrs": {"protocol": "rbd",
                                   "name": disk_name},
                            "hosts":  [{"name": host_ip,
                                     "port": host_port}]}
    :param disk_auth_dict: disk auth information, dict format like below
           disk_auth_dict = {"auth_user": auth_user,
                             "secret_type": auth_sec_usage_type,
                             "secret_uuid": auth_sec_uuid}
    :return: disk xml object
    """
    disk_xml = Disk(type_name=type_name)
    disk_xml.device = disk_device
    disk_xml.target = {"dev": device_target, "bus": device_bus}
    driver_dict = {"name": "qemu", "type": device_format}
    disk_xml.driver = driver_dict
    if disk_src_dict:
        logging.debug("disk src dict is: %s" % disk_src_dict)
        disk_source = disk_xml.new_disk_source(**disk_src_dict)
        disk_xml.source = disk_source
    if disk_auth_dict:
        logging.debug("disk auth dict is: %s" % disk_auth_dict)
        disk_xml.auth = disk_xml.new_auth(**disk_auth_dict)
    logging.debug("new disk xml in create_primitive_disk is: %s", disk_xml)
    return disk_xml


def create_custom_metadata_disk(disk_path, disk_format,
                                disk_device, device_target, device_bus, max_size, disk_inst=None):
    """
    Create another disk for a given path,customize driver metadata attribute

    :param disk_path: the path of disk
    :param disk_format: the format to disk image
    :param disk_device: the disk device type
    :param device_target: the target of disk
    :param device_bus: device bus
    :param max_size: metadata_cache max size
    :param disk_inst: disk instance
    :return: disk object if created or updated successfully
    """
    if disk_inst:
        custom_disk = disk_inst
    else:
        custom_disk = Disk(type_name='file')
    if disk_device:
        custom_disk.device = disk_device
    source_dict = {}
    if disk_path:
        source_dict.update({'file': disk_path})
    custom_disk.source = custom_disk.new_disk_source(
        **{"attrs": source_dict})
    if device_target:
        target_dict = {"dev": device_target, "bus": device_bus}
        custom_disk.target = target_dict
    driver_dict = {"name": "qemu", 'type': disk_format}
    # Create drivermetadata object
    new_one_drivermetadata = custom_disk.new_drivermetadata(**{"attrs": driver_dict})
    metadata_cache_dict = {"max_size": max_size, "max_size_unit": "bytes"}
    # Attach metadatacache into drivermetadata object
    new_one_drivermetadata.metadata_cache = custom_disk.DriverMetadata().new_metadatacache(**metadata_cache_dict)
    custom_disk.drivermetadata = new_one_drivermetadata
    logging.debug("disk xml in create_custom_metadata_disk: %s\n", custom_disk)
    return custom_disk