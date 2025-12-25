from dataclasses import dataclass
from typing import Any, Iterable, List, Tuple, Type

from dcim.models import (
    Interface, FrontPort, RearPort,
    ConsolePort, ConsoleServerPort,
    PowerPort, PowerOutlet,
    DeviceBay, ModuleBay,
    InventoryItem,
)

def get_custom_field_value(obj, field_name: str):
    # Same idea as your current plugin helper
    if hasattr(obj, "custom_field_data"):
        return obj.custom_field_data.get(field_name)
    if hasattr(obj, "cf") and isinstance(obj.cf, dict):
        return obj.cf.get(field_name)
    try:
        return obj.custom_fields.get(field_name)
    except Exception:
        return None

def set_custom_field_value(obj, field_name: str, value: Any) -> bool:
    """
    Set custom field value on an ORM object.
    Returns True if a change was applied.
    """
    current = get_custom_field_value(obj, field_name)
    if current == value:
        return False

    if hasattr(obj, "custom_field_data"):
        obj.custom_field_data[field_name] = value
        return True
    if hasattr(obj, "cf") and isinstance(obj.cf, dict):
        obj.cf[field_name] = value
        return True

    # Fallback (should rarely be needed):
    if hasattr(obj, "custom_fields") and isinstance(obj.custom_fields, dict):
        obj.custom_fields[field_name] = value
        return True

    return False

@dataclass(frozen=True)
class ComponentInfo:
    model: str
    id: int
    name: str
    current_value: Any

def iter_device_components(device) -> Iterable[Tuple[str, Any]]:
    """
    Yields tuples of (model_label, component_instance).
    """
    # Filter by device for each component type
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
