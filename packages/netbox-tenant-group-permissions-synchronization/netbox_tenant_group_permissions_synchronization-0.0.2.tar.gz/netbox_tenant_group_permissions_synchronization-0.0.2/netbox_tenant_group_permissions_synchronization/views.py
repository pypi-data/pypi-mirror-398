# views.py
import logging

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from dcim.models import Device

from .utils import (
    ComponentInfo,
    get_custom_field_value,
    get_device_tenant_group_id,
    iter_device_components,
    set_custom_field_value,
)

logger = logging.getLogger(__name__)

CF_NAME = "tenant_group_permissions"


class DevicePermissionsSyncView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Sync tenant_group_permissions from Device's tenant.group.id to all its components.
    """
    permission_required = ("dcim.view_device", "dcim.change_device")

    def get(self, request, device_id):
        try:
            device = Device.objects.get(pk=device_id)
        except Device.DoesNotExist:
            messages.error(request, f"Device with ID {device_id} not found")
            return redirect("dcim:device_list")

        try:
            tenant_group_id = get_device_tenant_group_id(device)

            to_sync = []
            synced = []
            total = 0

            for label, comp in iter_device_components(device):
                total += 1
                current = get_custom_field_value(comp, CF_NAME)

                comp_name = getattr(comp, "name", None) or str(comp)
                info = ComponentInfo(
                    model=label,
                    id=comp.id,
                    name=comp_name,
                    current_value=current,
                )

                if current != tenant_group_id:
                    to_sync.append(info)
                else:
                    synced.append(info)

            return render(
                request,
                "netbox_tenant_group_permissions_synchronization/device_permissions_sync.html",
                {
                    "device": device,
                    "cf_name": CF_NAME,
                    "tenant_group_id": tenant_group_id,
                    "components_to_sync": to_sync,
                    "components_synced": synced,
                    "components_total": total,
                },
            )

        except Exception as e:
            logger.error("GET error", exc_info=True)
            messages.error(request, f"An error occurred: {e}")
            return redirect("dcim:device", pk=device_id)

    def post(self, request, device_id):
        try:
            device = Device.objects.get(pk=device_id)
        except Device.DoesNotExist:
            messages.error(request, f"Device with ID {device_id} not found")
            return redirect("dcim:device_list")

        try:
            tenant_group_id = get_device_tenant_group_id(device)

            if tenant_group_id is None:
                messages.error(
                    request,
                    "Device has no tenant or the tenant has no tenant group. Nothing to synchronize.",
                )
                return redirect(request.path)

            updated = 0
            failed = 0

            for label, comp in iter_device_components(device):
                try:
                    changed = set_custom_field_value(comp, CF_NAME, tenant_group_id)
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
                messages.warning(
                    request,
                    f"Failed to update {failed} component(s). Check NetBox logs.",
                )

            return redirect(request.path)

        except Exception as e:
            logger.error("POST error", exc_info=True)
            messages.error(request, f"An error occurred: {e}")
            return redirect(request.path)
