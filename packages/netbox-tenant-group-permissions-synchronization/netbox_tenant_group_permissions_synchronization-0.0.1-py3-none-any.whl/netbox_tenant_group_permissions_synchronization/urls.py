from django.urls import path
from . import views

urlpatterns = [
    path("sync/<int:device_id>/", views.DevicePermissionsSyncView.as_view(), name="device_permissions_sync"),
]
