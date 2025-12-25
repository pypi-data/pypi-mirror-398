from django.db import models
from django.utils.translation import gettext as _
from netbox.models import NetBoxModel


class NetpickerSetting(NetBoxModel):
    unset_api_key = 'ey...'

    server_url = models.CharField(verbose_name=_("URL"))
    api_key = models.CharField(default=unset_api_key)
    tenant = models.CharField(default='default', max_length=250, verbose_name=_("Tenant"))
    last_synced = models.DateTimeField(blank=True, auto_now=True, null=True, editable=False)
    connection_status = models.CharField(max_length=50, editable=False, null=True, default='')

    class Meta:
        verbose_name = "netpickersetting"
        verbose_name_plural = "netpickersettings"

    def __str__(self):
        return f"{self.server_url}"

    def get_absolute_url(self):
        return '/'
