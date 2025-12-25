# netbox-tenant-group-permissions-synchronization

## Overview

This plugin allows you to compare and synchronize the **`tenant_group_permissions`** custom field from a **Device** to all of its associated **components** in NetBox.

It is designed to ensure that interfaces, ports, bays, and inventory items inherit the same tenant group–based permission model as their parent device, reducing configuration drift and manual errors.

---

## Features

* Synchronize `tenant_group_permissions` from a Device to all components
* Supports common DCIM components:

  * Interfaces
  * Front / Rear ports
  * Console ports / Console server ports
  * Power ports / Power outlets
  * Device bays / Module bays
  * Inventory items
* Clear comparison view before applying changes
* One-click synchronization of all out-of-sync components
* Safe updates (no change applied if values already match)
* Native NetBox ORM integration (no external API calls)

---

## Compatibility

Tested with:

* NetBox **4.3.7**

---

## Installation

If your NetBox installation uses a virtualenv, activate it first:

```bash
source /opt/netbox/venv/bin/activate
```

### Install from source

Clone the repository and install the plugin:

```bash
pip install .
```

### Enable the plugin

Add the plugin to the `PLUGINS` list in `configuration.py` (usually located at `/opt/netbox/netbox/netbox/`):

```python
PLUGINS = [
    'netbox_tenant_group_permissions_synchronization'
]
```

Restart NetBox services:

```bash
sudo systemctl restart netbox netbox-rq
```

---

## Usage

1. Navigate to a **Device** in NetBox
2. Click **"Sync Tenant Group Permissions"** at the top of the device page
3. Review the synchronization status:

   * Components needing synchronization (highlighted)
   * Components already synchronized
4. Click **"Sync All Components"** to apply the device value to all components

The page provides a read-only preview before changes are applied.

---

## Custom Fields Required

This plugin requires the following custom field to exist in NetBox:

### `tenant_group_permissions`

* **Type**: Must match your permission model (commonly *Object* or *Multiple Objects*)
* **Applied to**:

  * DCIM > Device
  * DCIM > Interface
  * DCIM > Front Port
  * DCIM > Rear Port
  * DCIM > Console Port
  * DCIM > Console Server Port
  * DCIM > Power Port
  * DCIM > Power Outlet
  * DCIM > Device Bay
  * DCIM > Module Bay
  * DCIM > Inventory Item

The plugin copies the value **as-is** from the device to each component.

---

## How It Works

1. The plugin reads the `tenant_group_permissions` value from the device
2. All associated components are enumerated via the NetBox ORM
3. Each component’s value is compared with the device value
4. Components with mismatched values are flagged for synchronization
5. On confirmation, the device value is written to each out-of-sync component

No changes are made to components that already match the device value.

---

## Permissions Required

Users must have at least:

* `dcim.view_device`
* `dcim.change_device`

Additional component-level change permissions may be required depending on your NetBox RBAC configuration.

---

## Troubleshooting

### Button not visible on device page

* Ensure the plugin is listed in `PLUGINS`
* Restart NetBox after installation
* Verify you have permission to view the device

### Components not updating

* Confirm the `tenant_group_permissions` custom field exists
* Ensure the field is assigned to all required component models
* Verify the custom field type matches your expected data structure

### Permission denied errors

* Ensure your user account has change permissions on the relevant DCIM objects
* Check NetBox RBAC rules for component models

---

## License

GNU General Public License v3.0 – see the LICENSE file for details.

---

## Acknowledgements

This plugin follows the same architectural pattern as the IP permissions synchronization plugin, adapted for device-to-component permission inheritance.
