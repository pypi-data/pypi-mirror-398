import logging
from functools import partial

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from dcim.models import Device, Interface
from ipam.models import IPAddress

from netpicker.models import MappedDevice
from ipaddress import ip_interface, ip_address

log = logging.getLogger(__name__)


@receiver(pre_save, sender=Device)
def handle_device_pre_change(sender, instance, **kwargs):
    original = Device.objects.filter(pk=instance.pk).first()
    instance._original_primary_ip4 = original.primary_ip4 if original else None
    instance._original_primary_ip6 = original.primary_ip6 if original else None


@receiver(post_save, sender=Device)
def handle_device_change(sender, instance, created, **kwargs):
    """
    Handle Device model changes, including primary IP changes.
    """
    if created:
        if (ipv4 := instance.primary_ip4) is not None:
            handle_device_primary_ip_change(instance, None, ipv4, ip_version=4)
        if (ipv6 := instance.primary_ip6) is not None:
            handle_device_primary_ip_change(instance, None, ipv6, ip_version=6)
    else:
        handler = partial(handle_device_primary_ip_change, instance)
        if instance._original_primary_ip4 != instance.primary_ip4:
            handler(instance._original_primary_ip4, instance.primary_ip4, ip_version=4)

        if instance._original_primary_ip6 != instance.primary_ip6:
            handler(instance._original_primary_ip6, instance.primary_ip6, ip_version=6)


@receiver(pre_save, sender=IPAddress)
def handle_ip_address_pre_change(sender, instance, **kwargs):
    """
    Handle the IP address before it's changed.
    Store the original assigned object for comparison.
    """
    if instance.pk:  # Only for existing objects
        if original := IPAddress.objects.get(pk=instance.pk):
            instance._original_assigned_object = original.assigned_object
            instance._original_address = original.address
            instance._original = original
        else:
            instance._original_assigned_object = None
            instance._original_address = None
            instance._original = None


@receiver(post_save, sender=IPAddress)
def handle_ip_address_change(sender: IPAddress, instance: IPAddress, created: bool, **kwargs):
    """
    Handle IP address changes for device interfaces.
    Triggered when an IPAddress is saved (created or updated).
    """
    # Check if the IP address is assigned to an interface
    if instance.assigned_object_type and instance.assigned_object:
        # Get the content type for the Interface model
        interface_ct = ContentType.objects.get_for_model(Interface)

        # Check if the assigned object is an Interface
        if instance.assigned_object_type == interface_ct:
            interface = instance.assigned_object
            device = interface.device
            if device.primary_ip4_id == instance.pk:
                handle_device_primary_ip_change(device, instance._original, instance, ip_version=4)
            if device.primary_ip6_id == instance.pk:
                handle_device_primary_ip_change(device, instance._original, instance, ip_version=6)


def _to_host_ip_str(addr) -> str | None:
    """
    Normalize various address representations to a host IP string.
    Accepts:
      - netaddr.IPNetwork / ipaddress.IPv[4|6]Interface (has .ip)
      - NetBox IPAddress.address (may be object or str "x.x.x.x/yy")
      - plain strings "x.x.x.x[/yy]" or "::1[/yy]"
    Returns:
      - "x.x.x.x" or "::1", or None if input is None
    """
    if addr is None:
        return None

    # If it's an object with .ip (netaddr.IPNetwork / ip_interface-like)
    ip_obj = getattr(addr, "ip", None)
    if ip_obj is not None:
        return str(ip_obj)

    # If it's a NetBox IPAddress with an 'address' attribute
    if hasattr(addr, "address"):
        inner = addr.address
        ip_obj = getattr(inner, "ip", None)
        if ip_obj is not None:
            return str(ip_obj)
        addr = inner  # fall through if it's actually a string

    # At this point, treat it as a string
    s = str(addr)
    try:
        if "/" in s:
            return str(ip_interface(s).ip)
        else:
            return str(ip_address(s))
    except ValueError:
        # Last resort: strip CIDR manually if present
        return s.split("/", 1)[0]


def handle_device_primary_ip_change(
        device: Device,
        old_ip: IPAddress | None,
        new_ip: IPAddress | None,
        ip_version: int
) -> None:
    """
    Handle when a device's primary IP is changed.

    Args:
        device: Device instance
        old_ip: Previous IPAddress instance (can be None)
        new_ip: New IPAddress instance (can be None)
        ip_version: 4 or 6
    """
    # Normalize to plain host IP strings
    old_host = _to_host_ip_str(getattr(old_ip, "address", old_ip)) if old_ip else None
    new_host = _to_host_ip_str(getattr(new_ip, "address", new_ip)) if new_ip else None

    # If nothing changes, bail early
    if old_host and new_host and old_host == new_host:
        return

    if old_host:
        MappedDevice.objects.filter(ipaddress=old_host).update(netbox=None)

    if new_host:
        MappedDevice.objects.filter(ipaddress=new_host).update(netbox=device)
