import logging
import traceback
from netbox.plugins import PluginTemplateExtension

logger = logging.getLogger(__name__)

class DeviceViewExtension(PluginTemplateExtension):
    models = ["dcim.device"]

    def buttons(self):
        try:
            obj = self.context.get("object")
            if not obj:
                return ""

            return self.render(
                "netbox_tenant_group_permissions_synchronization/sync_device_permissions_button.html",
                extra_context={"device": obj},
            )

        except Exception as e:
            logger.error(f"Error in DeviceViewExtension.buttons(): {type(e).__name__}: {e}")
            logger.error(traceback.format_exc())
            return ""

template_extensions = [DeviceViewExtension]
