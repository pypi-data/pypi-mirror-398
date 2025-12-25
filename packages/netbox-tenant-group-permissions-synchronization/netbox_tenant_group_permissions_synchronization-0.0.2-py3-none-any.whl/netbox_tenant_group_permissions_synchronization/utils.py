# utils.py
from dataclasses import dataclass
from typing import Any, Iterable, List, Tuple

from dcim.models import (
    Interface,
    FrontPort,
    RearPort,
    ConsolePort,
    ConsoleServerPort,
    PowerPort,
    PowerOutlet,
    DeviceBay,
    ModuleBay,
    InventoryItem,
)


def get_custom_field_value(obj, field_name: str) -> Any:
    """
    Read a custom field value from an ORM object in a NetBox-version-tolerant way.
    """
    if hasattr(obj, "custom_field_data") and isinstance(obj.custom_field_data, dict):
        return obj.custom_field_data.get(field_name)

    # Some contexts expose 'cf' dict
    if hasattr(obj, "cf") and isinstance(obj.cf, dict):
        return obj.cf.get(field_name)

    # Some serializers expose 'custom_fields' dict (read-only in many cases)
    if hasattr(obj, "custom_fields") and isinstance(obj.custom_fields, dict):
        return obj.custom_fields.get(field_name)

    return None


def set_custom_field_value(obj, field_name: str, value: Any) -> bool:
    """
    Set a custom field value on an ORM object.
    Returns True if a change was applied, False if no change was needed.
    """
    current = get_custom_field_value(obj, field_name)
    if current == value:
        return False

    if hasattr(obj, "custom_field_data") and isinstance(obj.custom_field_data, dict):
        obj.custom_field_data[field_name] = value
        return True

    if hasattr(obj, "cf") and isinstance(obj.cf, dict):
        obj.cf[field_name] = value
        return True

    if hasattr(obj, "custom_fields") and isinstance(obj.custom_fields, dict):
        obj.custom_fields[field_name] = value
        return True

    return False


def get_device_tenant_group_id(device) -> int | None:
    """
    Return device.tenant.group.id as an integer, or None if no tenant/group.
    This is the source-of-truth for tenant_group_permissions sync.
    """
    if not device or not getattr(device, "tenant_id", None):
        return None

    tenant = getattr(device, "tenant", None)
    if not tenant or not getattr(tenant, "group_id", None):
        return None

    return int(tenant.group_id)


@dataclass(frozen=True)
class ComponentInfo:
    model: str
    id: int
    name: str
    current_value: Any


def iter_device_components(device) -> Iterable[Tuple[str, Any]]:
    """
    Yield (label, component_instance) for supported component types belonging to device.
    """
    queryset_map: List[Tuple[str, Any]] = [
        ("interfaces", Interface.objects.filter(device=device)),
        ("front_ports", FrontPort.objects.filter(device=device)),
        ("rear_ports", RearPort.objects.filter(device=device)),
        ("console_ports", ConsolePort.objects.filter(device=device)),
        ("console_server_ports", ConsoleServerPort.objects.filter(device=device)),
        ("power_ports", PowerPort.objects.filter(device=device)),
        ("power_outlets", PowerOutlet.objects.filter(device=device)),
        ("module_bays", ModuleBay.objects.filter(device=device)),
        ("device_bays", DeviceBay.objects.filter(device=device)),
        ("inventory_items", InventoryItem.objects.filter(device=device)),
    ]

    for label, qs in queryset_map:
        for obj in qs:
            yield label, obj
