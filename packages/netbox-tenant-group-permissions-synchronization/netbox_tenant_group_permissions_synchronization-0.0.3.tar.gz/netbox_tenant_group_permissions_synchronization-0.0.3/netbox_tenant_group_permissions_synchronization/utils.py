# utils.py
from dataclasses import dataclass
from typing import Any, Iterable, List, Tuple, Optional

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
from extras.models import CustomField


CF_NAME = "tenant_group_permissions"


def get_custom_field_def(field_name: str) -> Optional[CustomField]:
    try:
        return CustomField.objects.get(name=field_name)
    except CustomField.DoesNotExist:
        return None


def normalize_cf_value(cf_def: Optional[CustomField], raw_value: Any) -> Any:
    """
    Convert a scalar tenant_group_id into the correct shape for the CF type.
    """
    if cf_def is None:
        # If we can't detect, do nothing (best-effort).
        return raw_value

    cf_type = (cf_def.type or "").lower()

    # NetBox uses 'multiobject' / 'multipleobject' internally depending on version.
    if cf_type in ("multiobject", "multipleobject", "multiple_objects", "multiple objects"):
        if raw_value is None:
            return []
        # Ensure list
        if isinstance(raw_value, list):
            return raw_value
        return [raw_value]

    # Single object
    if cf_type in ("object",):
        return raw_value  # scalar id is OK

    # Integer/text/etc
    return raw_value


def get_custom_field_value(obj, field_name: str) -> Any:
    if hasattr(obj, "custom_field_data") and isinstance(obj.custom_field_data, dict):
        return obj.custom_field_data.get(field_name)
    if hasattr(obj, "cf") and isinstance(obj.cf, dict):
        return obj.cf.get(field_name)
    if hasattr(obj, "custom_fields") and isinstance(obj.custom_fields, dict):
        return obj.custom_fields.get(field_name)
    return None


def set_custom_field_value(obj, field_name: str, value: Any, cf_def: Optional[CustomField] = None) -> bool:
    """
    Set CF value with correct data shape.
    Returns True if changed.
    """
    value = normalize_cf_value(cf_def, value)
    current = get_custom_field_value(obj, field_name)

    # Compare safely for list vs scalar
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


def get_device_tenant_group_id(device) -> Optional[int]:
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
