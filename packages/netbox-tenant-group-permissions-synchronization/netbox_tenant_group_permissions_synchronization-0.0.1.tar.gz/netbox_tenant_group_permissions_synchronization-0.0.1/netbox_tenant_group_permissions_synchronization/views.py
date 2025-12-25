import logging
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from dcim.models import Device

from .utils import (
    ComponentInfo,
    get_custom_field_value,
    iter_device_components,
    set_custom_field_value,
)

logger = logging.getLogger(__name__)

CF_NAME = "tenant_group_permissions"

class DevicePermissionsSyncView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Sync tenant_group_permissions from Device to all its components.
    """
    permission_required = ("dcim.view_device", "dcim.change_device")

    def get(self, request, device_id):
        try:
            device = Device.objects.get(pk=device_id)
        except Device.DoesNotExist:
            messages.error(request, f"Device with ID {device_id} not found")
            return redirect("dcim:device_list")

        try:
            device_cf_value = get_custom_field_value(device, CF_NAME)

            to_sync = []
            synced = []
            total = 0

            for label, comp in iter_device_components(device):
                total += 1
                current = get_custom_field_value(comp, CF_NAME)

                # Build a readable name fallback
                comp_name = getattr(comp, "name", None) or str(comp)

                info = ComponentInfo(
                    model=label,
                    id=comp.id,
                    name=comp_name,
                    current_value=current,
                )

                if current != device_cf_value:
                    to_sync.append(info)
                else:
                    synced.append(info)

            return render(
                request,
                "netbox_tenant_group_permissions_synchronization/device_permissions_sync.html",
                {
                    "device": device,
                    "cf_name": CF_NAME,
                    "device_cf_value": device_cf_value,
                    "components_to_sync": to_sync,
                    "components_synced": synced,
                    "components_total": total,
                },
            )

        except Exception as e:
            logger.error(f"GET error: {e}", exc_info=True)
            messages.error(request, f"An error occurred: {e}")
            return redirect("dcim:device", pk=device_id)

    def post(self, request, device_id):
        try:
            device = Device.objects.get(pk=device_id)
        except Device.DoesNotExist:
            messages.error(request, f"Device with ID {device_id} not found")
            return redirect("dcim:device_list")

        try:
            device_cf_value = get_custom_field_value(device, CF_NAME)

            updated = 0
            failed = 0

            for label, comp in iter_device_components(device):
                try:
                    changed = set_custom_field_value(comp, CF_NAME, device_cf_value)
                    if changed:
                        comp.save()
                        updated += 1
                except Exception as e:
                    failed += 1
                    logger.error(f"Failed updating {label} id={comp.id}: {e}", exc_info=True)

            if updated:
                messages.success(request, f"Synchronized {updated} component(s).")
            else:
                messages.info(request, "No changes needed.")

            if failed:
                messages.warning(request, f"Failed to update {failed} component(s). Check logs.")

            return redirect(request.path)

        except Exception as e:
            logger.error(f"POST error: {e}", exc_info=True)
            messages.error(request, f"An error occurred: {e}")
            return redirect(request.path)
