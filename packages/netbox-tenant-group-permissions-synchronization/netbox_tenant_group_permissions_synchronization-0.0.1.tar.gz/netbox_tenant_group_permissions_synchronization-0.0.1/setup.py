import os
from setuptools import setup

_version_file = os.path.join(
    os.path.dirname(__file__),
    "netbox_tenant_group_permissions_synchronization",
    "_version.py",
)

_version_data = {}
with open(_version_file, encoding="utf-8") as f:
    exec(f.read(), _version_data)

setup(
    name="netbox_tenant_group_permissions_synchronization",
    version=_version_data["__version__"],
    description=_version_data["__description__"],
    long_description="",
    long_description_content_type="text/markdown",
    author=_version_data["__author__"],
    author_email=_version_data["__author_email__"],
    license=_version_data["__license__"],
    packages=["netbox_tenant_group_permissions_synchronization"],
    package_data={
        "netbox_tenant_group_permissions_synchronization": [
            "templates/netbox_tenant_group_permissions_synchronization/*.html"
        ]
    },
    zip_safe=False,
)
