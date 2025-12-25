import re
from contextlib import suppress

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import HiddenInput, TextInput
from django.utils.safestring import SafeText
from django.utils.translation import gettext_lazy as _
from netaddr import AddrFormatError
from netaddr.ip import IPNetwork

from dcim.models import Device, Module
from netbox.forms import NetBoxModelForm
from netpicker import models
from netpicker import client
from netpicker.models import MappedDevice
from utilities.forms.fields import DynamicModelChoiceField


re_commands = re.compile(r'(?:[^{]*(\{[a-zA-Z_]\w*})??[^{]*)??',
                         re.MULTILINE | re.DOTALL)


def validate_identifier(value):
    if isinstance(value, str) and value.isidentifier():
        return value
    raise ValidationError(f'{value} is not a valid identifier')


def validate_command(value):
    if not re_commands.fullmatch(value):
        raise ValidationError('Invalid commands specified')


class DeviceComponentForm(NetBoxModelForm):
    device = DynamicModelChoiceField(
        label=_('Device'),
        queryset=Device.objects.all(),
        selector=True,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Disable reassignment of Device when editing an existing instance
        if self.instance.pk:
            self.fields['device'].disabled = False


class ModularDeviceComponentForm(DeviceComponentForm):
    module = DynamicModelChoiceField(
        label=_('Module'),
        queryset=Module.objects.all(),
        required=False,
        query_params={
            'device_id': '$device',
        }
    )


class PlatformMultipleChoiceField(forms.MultipleChoiceField):
    def __init__(self, **kwargs):
        domains = client.get_domains()
        platforms = domains['platforms']
        choices = dict(zip(platforms, platforms))
        kwargs['choices'] = choices
        super().__init__(**kwargs)

    @staticmethod
    def get_choices():
        return PlatformMultipleChoiceField(
            label=_('Platforms'),
            required=False,
        )


class SettingsForm(NetBoxModelForm):
    server_url = forms.CharField(required=True, label=_('API url'),
                                 help_text=_('Netpicker API base url (root url)'))
    tenant = forms.CharField(required=True, label=_('Tenant'), help_text=_('Name of your Netpicker tenant'))
    api_key = forms.CharField(required=True, label=_('API key'), widget=TextInput(),
                              help_text=SafeText('Key obtained from <a id="np-admin" href="" target="_blank">'
                                                 'Netpicker API admin</a>'))

    class Meta:
        model = models.NetpickerSetting
        fields = ['server_url', 'api_key', 'tenant']


class JobEditForm(NetBoxModelForm):
    name = forms.CharField(
        required=True,
        label=_('Name'),
        help_text=_("The job's unique name"),
        validators=[validate_identifier]
    )
    commands = forms.CharField(
        required=True,
        validators=[validate_command],
        widget=forms.Textarea(attrs={
            'rows': 15,
            'cols': 80,
            'placeholder': 'Enter CLI configure commands separated by new-line...',
            'class': 'form-control .monospaced'
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['platforms'] = PlatformMultipleChoiceField()

        if self.instance and self.instance.commands:
            cmds = '\n'.join(self.instance.commands)
            self.initial['commands'] = cmds

    def clean_commands(self):
        commands = self.cleaned_data['commands']
        cleared = [n.strip() for n in commands.splitlines()]
        return cleared

    def save(self, commit=True):
        client.save_job(self.instance)
        self.instance.pk = self.instance.name
        return self.instance

    class Meta:
        model = models.Job
        fields = 'name', 'platforms', 'commands'


def valid_ip(s):
    with suppress(ValueError, AddrFormatError):
        return IPNetwork(s)


def platform_matches_pattern(platform: str, pattern: str) -> bool:
    """
    Check if a platform matches a pattern.
    - '*' matches all platforms
    - 'cisco*' matches platforms starting with 'cisco' (case-insensitive)
    - Exact matches also work
    """
    if not platform or not pattern:
        return False

    # '*' matches all
    if pattern == '*':
        return True

    # Convert to lowercase for case-insensitive matching
    platform_lower = platform.lower()
    pattern_lower = pattern.lower()

    # If pattern ends with '*', check if platform starts with the prefix
    if pattern_lower.endswith('*'):
        prefix = pattern_lower[:-1]
        return platform_lower.startswith(prefix)

    # Exact match (case-insensitive)
    return platform_lower == pattern_lower


def platform_matches_any_pattern(platform: str, patterns: list[str]) -> bool:
    """Check if a platform matches any of the given patterns."""
    if not patterns:
        return True
    return any(platform_matches_pattern(platform, pattern) for pattern in patterns)


def get_job_exec_form(job: models.Job, fixtures):

    params = {p.name: p for p in job.signature.params if p.name not in set(fixtures)}
    variables = params.keys()

    if job.platforms:
        # Build Q objects for pattern matching
        platform_filters = Q()
        has_wildcard = False

        for pattern in job.platforms:
            if pattern == '*':
                has_wildcard = True
                break
            elif pattern.endswith('*'):
                # Pattern like 'cisco*' - match platforms starting with prefix
                prefix = pattern[:-1]
                platform_filters |= Q(platform__istartswith=prefix)
            else:
                # Exact match (case-insensitive)
                platform_filters |= Q(platform__iexact=pattern)

        if has_wildcard:
            # '*' means all devices, so no platform filter needed
            selectables = MappedDevice.objects.values('netbox_id')
        else:
            selectables = MappedDevice.objects.filter(platform_filters).values('netbox_id')

        mapped_netbox_ids = set(selectables.values_list('netbox_id', flat=True))
        qs = Device.objects.filter(pk__in=mapped_netbox_ids)
    else:
        selectables = MappedDevice.objects.values('netbox_id')
        mapped_netbox_ids = set(selectables.values_list('netbox_id', flat=True))
        qs = Device.objects.filter(pk__in=mapped_netbox_ids)

    all_netpicker_devices = client.get_netpicker_devices()

    mapped_ips = set(
        MappedDevice.objects.filter(
            netbox_id__isnull=False
        ).values_list('ipaddress', flat=True)
    )

    choices = []

    for device in qs:
        choices.append((f"device:{device.pk}", f"{device.name}"))

    for ip, platform, tenant, name in all_netpicker_devices:
        # Filter NetPicker devices by platform if job has platforms specified
        if job.platforms and not platform_matches_any_pattern(platform, job.platforms):
            continue
        if ip not in mapped_ips:
            display_name = name if name else ip
            choices.append((f"ip:{ip}", f"{display_name}"))

    dev_field = forms.MultipleChoiceField(
        choices=choices,
        help_text=('All devices known to Netpicker by IP address. '
                   'Devices are filtered by platform(s) specified by the job. '
                   'If no platforms are specified, all devices are included.')
    )
    devices = dict(devices=dev_field)
    vars = {v: forms.CharField(label=v, required=params[v].has_default is False) for v in variables}
    meta = dict(Meta=type('Meta', tuple(), dict(model=models.Job, fields=variables)))
    misc = dict(confirm=forms.BooleanField(required=False, widget=HiddenInput()))
    attrs = devices | vars | misc | meta | dict(field_order=['devices', *variables])
    cls = type(forms.ModelForm)(f"Job_{job.signature}", (forms.ModelForm,), attrs)
    return cls
