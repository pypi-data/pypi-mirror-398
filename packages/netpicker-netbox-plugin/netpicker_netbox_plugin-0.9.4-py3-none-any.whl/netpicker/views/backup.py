from datetime import UTC, datetime, timedelta

import requests
from django.http import HttpRequest, StreamingHttpResponse
from django.utils.safestring import SafeText
from django.utils.translation import gettext_lazy as _
from django.views import View

from dcim.models import Device
from dcim.views import DeviceComponentsView
from netbox.views import generic
from netbox.object_actions import CloneObject, DeleteObject, EditObject
from netpicker.client import (
    download_config, get_device_readouts, get_readout_history,
    search_configs_with_error_handling
)
from netpicker.models import (
    Backup, BackupHistory, BackupSearchHit, MappedDevice, ProxyQuerySet
)
from netpicker import tables
from netpicker.utilities import get_logo, get_settings
from netpicker.views.base import RequireSettingsMixin
from utilities.views import ViewTab, register_model_view


def get_label(prefix: str) -> SafeText:
    fmt_logo = get_logo(style="width:16px; vertical-align:top")
    result = SafeText(_(prefix) + ' ') + fmt_logo
    return result


class BackupProxyMixin:
    def get_object(self, **kwargs):
        backup = Backup()
        if pk := kwargs.get('pk'):
            backup.id = pk
            try:
                ipaddress, config_id = pk.rsplit('-', 1)
            except ValueError:
                backup.preview = None
                backup._error_message = "Invalid backup ID format"
                return backup

            try:
                backup.preview = download_config(ipaddress, config_id)
                backup._error_message = None
            except Exception as e:
                backup.preview = None
                backup._error_message = str(e)
        return backup

    def get_queryset(self, request: HttpRequest):
        # this is a fake method to satisfy the view protocol
        return ProxyQuerySet(model=Backup)


class ConditionalViewTab(ViewTab):
    def render(self, instance):
        request = getattr(instance._meta, 'current_request', None)
        if request and (settings := get_settings(request)):
            # Match by device name instead of IP address (case-insensitive)
            is_mapped = MappedDevice.objects.filter(
                tenant=settings.tenant,
                name__iexact=instance.name
            ).first()
            if is_mapped:
                return super().render(instance)
        return {}


@register_model_view(Device, 'backups', path="netpicker/backups")
class DeviceBackupsView(RequireSettingsMixin, DeviceComponentsView):
    child_model = Backup
    force_redirect = False
    table = tables.DeviceBackupTable
    actions = (CloneObject, DeleteObject, EditObject)
    template_name = 'netpicker/backups.html'
    tab = ConditionalViewTab(
        label=get_label('Backups'),
        badge=None,
        permission='dcim.view_backups',
        weight=620,
        hide_if_empty=False
    )

    def get_children(self, request, parent):
        if request.settings:
            # Match by device name instead of IP address
            mapped_device = MappedDevice.objects.filter(
                tenant=request.settings.tenant,
                name=parent.name
            ).first()
            if mapped_device:
                try:
                    return get_device_readouts(parent.id, mapped_device.ipaddress)
                except Exception:
                    return []
        return []


@register_model_view(Backup)
class BackupPreviewView(RequireSettingsMixin, BackupProxyMixin, generic.ObjectView):
    template_name = 'netpicker/backup.preview.html'

    def get_extra_context(self, request, instance):
        context = super().get_extra_context(request, instance)
        if instance:
            context['error_message'] = getattr(instance, '_error_message', None)
        return context


@register_model_view(Backup, name='download')
class BackupDownloadView(View):
    def dispatch(self, request: HttpRequest, *args, **kwargs):
        settings = get_settings(request)
        pk = request.resolver_match.kwargs.get('pk')
        ipaddress, config_id = pk.rsplit('-', 1)
        url = f"{settings.server_url}/api/v1/devices/{settings.tenant}/{ipaddress}/configs/{config_id}"
        headers = {'authorization': f"Bearer {settings.api_key}"}
        r = requests.get(url, headers=headers, stream=True)
        resp = StreamingHttpResponse(streaming_content=r.raw)
        resp['content-disposition'] = f'attachment; filename="{pk}.backup"'
        return resp


@register_model_view(Device, 'backup-history', path="netpicker/history")
class DeviceBackupHistoryView(RequireSettingsMixin, DeviceComponentsView):
    child_model = BackupHistory
    force_redirect = False
    table = tables.DeviceBackupHistoryTable
    actions = (CloneObject, DeleteObject, EditObject)

    template_name = 'netpicker/backups_history.html'
    tab = ConditionalViewTab(
        label=get_label('Change history'),
        badge=None,
        permission='dcim.view_backups',
        weight=620,
        hide_if_empty=False
    )

    def get_children(self, request, parent):
        if request.settings:
            # Match by device name instead of IP address
            mapped_device = MappedDevice.objects.filter(
                tenant=request.settings.tenant,
                name=parent.name
            ).first()
            if mapped_device:
                start = datetime.now(UTC) - timedelta(days=30)
                after_param = request.GET.get('after')
                if after_param:
                    try:
                        datetime.strptime(after_param, '%Y-%m-%d')
                        after = after_param
                    except ValueError:
                        after = start.strftime('%Y-%m-%d')
                else:
                    after = start.strftime('%Y-%m-%d')
                return get_readout_history(mapped_device.ipaddress, after)
        return []

    def get_extra_context(self, request, parent):
        context = super().get_extra_context(request, parent)
        default_start = datetime.now(UTC) - timedelta(days=30)
        default_after = default_start.strftime('%Y-%m-%d')
        context['after_date'] = request.GET.get('after', default_after)
        return context


@register_model_view(BackupSearchHit, name='list', path='', detail=False)
class BackupSearch(RequireSettingsMixin, generic.ObjectListView):
    table = tables.DeviceBackupSearchTable
    template_name = 'netpicker/backup_search.html'
    actions = ()

    def get_queryset(self, request):
        q = request.GET.get('q')
        if q:
            hits, error_occurred = search_configs_with_error_handling(q)
            # Store error flag in request for use in template
            request.api_error_occurred = error_occurred
        else:
            hits = []
            request.api_error_occurred = False
        return ProxyQuerySet(model=BackupSearchHit, data=hits)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['api_error_occurred'] = getattr(self.request, 'api_error_occurred', False)
        return context
