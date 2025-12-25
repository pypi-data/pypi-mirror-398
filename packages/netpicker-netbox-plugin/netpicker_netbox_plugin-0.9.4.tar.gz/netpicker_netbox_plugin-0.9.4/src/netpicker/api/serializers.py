from netbox.api.serializers import NetBoxModelSerializer

from netpicker.models import NetpickerSetting


__all__ = 'NetpickerSettingSerializer',


class NetpickerSettingSerializer(NetBoxModelSerializer):
    class Meta:
        model = NetpickerSetting
        fields = ('id', 'server_url', 'api_key', 'tenant')
