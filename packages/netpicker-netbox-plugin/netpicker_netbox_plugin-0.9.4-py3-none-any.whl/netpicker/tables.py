from dataclasses import replace

import django_tables2 as tables
from django.urls import NoReverseMatch, reverse
from django.utils.html import escape
from django.utils.safestring import SafeText
from django.utils.translation import gettext_lazy as _

from netbox.tables import ActionsColumn, BaseTable, NetBoxTable
from netbox.tables.columns import ActionsItem
from netpicker import models
from netpicker.utilities import get_runnable_devices_query
from utilities.paginator import EnhancedPaginator, get_paginate_count


class ZeroOrphansPaginator(EnhancedPaginator):
    def __init__(self, object_list, per_page):
        super().__init__(object_list, per_page, 0)


class ActionLessMixin:
    actions = ()


class DownloadBackupColumn(ActionsColumn):
    actions = {
        'download': ActionsItem('Download', 'download', 'read', 'primary')
    }


def linkify_backup(*args, **kwargs):
    backup = kwargs['bound_row']._record
    return reverse('plugins:netpicker:backup', kwargs={'pk': backup.pk})


class DeviceBackupTable(NetBoxTable):
    upload_date = tables.Column(verbose_name=_('Backup date'), linkify=linkify_backup, attrs={'a': {'class': 'cfg'}})
    file_size = tables.Column(verbose_name=_('File size'), empty_values=(None, -1))
    initiator = tables.Column(verbose_name=_('Initiator'))
    readout_error = tables.Column(verbose_name=_('Error'))

    actions = DownloadBackupColumn(actions=('download',))

    class Meta(NetBoxTable.Meta):
        model = models.Backup
        fields = (
            'id', 'upload_date', 'file_size', 'initiator', 'readout_error',
        )
        default_columns = (
            'upload_date', 'file_size', 'initiator', 'readout_error',
        )
        attrs = {
            'class': 'table table-hover object-list netpicker-backups',
        }


def link_history(*args, **kwargs):
    settings = kwargs['table'].context['request'].settings
    base_url = settings.server_url
    tenant = settings.tenant
    record = kwargs['record']
    ipaddress = record['ipaddress']
    commit = record['commit']
    return f"{base_url}/tenant/{tenant}/backups/device/{ipaddress}?nav=history&commit={commit}"


class DeviceBackupHistoryTable(NetBoxTable):
    timestamp = tables.Column(verbose_name=_('Backup date'), linkify=link_history)
    deltas = tables.Column(verbose_name=_('+/-'), accessor='deltas')
    diff = tables.Column(verbose_name=_('diff'), accessor='diff', orderable=False)

    class Meta(NetBoxTable.Meta):
        model = models.BackupHistory
        fields = (
            'timestamp', 'deltas', 'diff'
        )
        default_columns = (
            'timestamp', 'deltas', 'diff'
        )
        attrs = {
            'class': 'table table-hover object-list netpicker-history',
        }

    def render_diff(self, value, record):
        def decorate(n):
            if n.startswith('+++') or n.startswith('---'):
                return n
            c = n[0]
            if c == '+':
                return f'<span style="color:green">{n}</span>'
            if c == '-':
                return f'<span style="color:red">{n}</span>'
            return n

        lines = ''.join(value).splitlines()[4:20]
        txt = '\n'.join((decorate(ln) for ln in lines))
        return SafeText(f'<pre class="code">{txt}</pre>')

    def render_timestamp(self, value, record):
        settings = self.context['request'].settings
        base_url = settings.server_url
        tenant = settings.tenant
        ipaddress = record['ipaddress']
        commit = record['commit']
        url = f"{base_url}/tenant/{tenant}/backups/device/{ipaddress}?nav=history&commit={commit}"
        return SafeText(f'<a href="{url}" target="_netpicker">{value} &#x1f517;</a>')


job_badge_colors = {
    'SUCCESS': 'text-bg-green',
    'PENDING': 'text-bg-cyan',
    'ERROR': 'text-bg-red',
    'FAILURE': 'text-bg-red',
    'SKIPPED': 'bg-grey',
}


class AutomationLogTable(NetBoxTable):
    exec_at = tables.Column(verbose_name=_('Executed at'), orderable=False)
    initiator = tables.Column(verbose_name=_('Initiator'), orderable=False)
    job_name = tables.Column(verbose_name=_('Job name'))
    status = tables.Column(verbose_name=_('Status'))

    id = tables.Column(
        linkify=True,
        verbose_name=_('ID')
    )

    actions = ActionsColumn(actions=tuple())

    class Meta(NetBoxTable.Meta):
        model = models.Log
        fields = (
            'id', 'job_name', 'status', 'exec_at', 'initiator'
        )
        default_columns = (
            'id', 'job_name', 'status', 'exec_at', 'initiator'
        )

    def render_status(self, value, record):
        v = value.value
        cls = job_badge_colors.get(v, ('white', 'white'))
        return SafeText(f'<span class="badge {cls}">{v}</span>')


class JobActionsColumn(ActionsColumn):
    run_action = ActionsItem('Execute', 'play', 'execute', 'primary')
    edit_action = ActionsItem('Edit', 'pencil', 'change', 'warning')

    def render(self, record, table, **kwargs):
        is_simple = getattr(record, 'is_simple', None)
        actions = {}
        runnable = bool(get_runnable_devices_query(record.platforms)) if record.platforms else True
        if runnable:
            actions['run'] = replace(self.run_action, css_class='primary')
        if is_simple and record.tags and 'netboxed' in record.tags:
            actions['edit'] = self.edit_action
        self.actions = actions
        return super().render(record, table, **kwargs)


class AutomationJobsTable(NetBoxTable):
    name = tables.Column(verbose_name=_('Name'), linkify=True)
    platforms = tables.Column(
        verbose_name=_('Platforms'),
        orderable=False
    )
    actions = JobActionsColumn()

    def render_platforms(self, value, record):
        """Render platforms as comma-separated list"""
        platforms = getattr(record, 'platforms', None)

        if platforms is None:
            return '—'
        if isinstance(platforms, list):
            if len(platforms) == 0:
                return '—'
            return ', '.join(str(p) for p in platforms if p)
        return str(platforms) if platforms else '—'

    class Meta(NetBoxTable.Meta):
        model = models.Job
        fields = (
            'name', 'platforms', 'actions'
        )
        default_columns = (
            'name', 'platforms'
        )


class SettingsTable(NetBoxTable):
    server_url = tables.Column(verbose_name=_('Netpicker API url'))
    api_key = tables.Column(verbose_name=_('API key'))
    tenant = tables.Column(verbose_name=_('Tenant'))

    class Meta(NetBoxTable.Meta):
        model = models.NetpickerSetting
        fields = (
            'server_url', 'api_key', 'tenant'
        )


def linkify_ip_device(*args, **kwargs):
    device_id = kwargs['bound_row']._record.device_id
    # Handle unmapped devices (device_id is None)
    if device_id is None:
        return None  # Don't create a link if device is not mapped
    try:
        url = reverse('dcim:device_backups', kwargs={'pk': device_id})
        return f"{url}?search=1"
    except NoReverseMatch:
        return None


def pre_content(value):
    return f'<pre style="padding: 0">{escape(value)}</pre>'


class DeviceBackupSearchTable(NetBoxTable):
    name = tables.Column(verbose_name=_('Name'), linkify=linkify_ip_device)
    ipaddress = tables.Column(verbose_name=_('IP address'), linkify=linkify_ip_device)
    matches = tables.Column(verbose_name=_('Matches'), orderable=False)

    actions = ()

    def render_matches(self, value, record):
        content = ''.join(
            [f"<tr><td>{row['line_number']}:</td><td>{pre_content(row['content'])}</td></tr>" for row in value])
        result = f'<table style="padding 0 2 0 2">{content}</table>'
        return SafeText(result)

    class Meta(NetBoxTable.Meta):
        model = models.BackupSearchHit
        fields = (
            'name', 'ipaddress', 'matches'
        )
        default_columns = (
            'name', 'ipaddress', 'matches'
        )


def linkify_mapped_device(*args, **kwargs):
    device_id = kwargs['bound_row']._record.netbox_id
    if device_id is None:
        return None
    url = reverse('dcim:device', kwargs={'pk': device_id})
    return url


class MappedDeviceTable(BaseTable):
    name = tables.Column(verbose_name=_('Name'), linkify=linkify_mapped_device)
    ipaddress = tables.Column(verbose_name=_('IP address'), linkify=linkify_mapped_device)
    platform = tables.Column(verbose_name=_('Platform'))

    def configure(self, request):
        super().configure(request)
        paginate = {
            'paginator_class': ZeroOrphansPaginator,
            'per_page': get_paginate_count(request)
        }
        tables.RequestConfig(request, paginate).configure(self)

    class Meta:
        model = models.MappedDevice
        fields = (
            'name', 'ipaddress', 'platform'
        )
        default_columns = (
            'name', 'ipaddress', 'platform'
        )
        attrs = {
            'class': 'table object-list',
        }
