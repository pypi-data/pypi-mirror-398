from django.contrib.postgres.fields import ArrayField
from django.db import models
from netpicker.models.base import NetpickerModel, ProxyQuerySet


class Backup(NetpickerModel):
    id = models.CharField(primary_key=True)
    commit = models.CharField()
    upload_date = models.DateTimeField()
    file_size = models.IntegerField()
    initiator = models.CharField()
    readout_error = models.TextField(null=True)

    device_id: str = None
    ipaddress: str = None
    preview: str = None

    objects = ProxyQuerySet.as_manager()

    class Meta:
        managed = False

    def get_absolute_url(self):
        return f'javascript:alert({self.id});'


class BackupHistory(NetpickerModel):
    timestamp = models.DateTimeField()
    diff = models.TextField()
    deltas = models.TextField()

    objects = ProxyQuerySet.as_manager()

    class Meta:
        managed = False


class BackupSearchHit(NetpickerModel):
    ipaddress = models.CharField()
    device_id = models.IntegerField()
    name = models.CharField()
    matches = ArrayField(models.JSONField())

    def __str__(self):
        return f"{self.ipaddress} ({self.device_id}) {len(self.matches)} matches"
