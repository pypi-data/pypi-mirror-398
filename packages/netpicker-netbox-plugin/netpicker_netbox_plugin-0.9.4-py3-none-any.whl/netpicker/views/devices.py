from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect

from netbox.views import generic
from netpicker import tables
from netpicker.models import MappedDevice
from netpicker.utilities import reload_devices
from netpicker.views.base import RequireSettingsMixin
from utilities.views import register_model_view


@register_model_view(MappedDevice, name='list', path='', detail=False)
class MappedDeviceListView(RequireSettingsMixin, generic.ObjectListView):
    table = tables.MappedDeviceTable
    actions = ()
    template_name = 'netpicker/devices_list.html'

    def get_queryset(self, request):
        queryset = MappedDevice.objects.all()
        q = request.GET.get('q')
        if q:
            filters = Q(ipaddress__icontains=q) | Q(platform__icontains=q)
            filters |= Q(name__isnull=False, name__icontains=q)
            queryset = queryset.filter(filters)
        return queryset

    def post(self, request, *args, **kwargs):
        try:
            reload_devices()
            messages.success(request, 'Devices refreshed successfully.')
        except Exception as e:
            messages.error(request, f'Error refreshing devices: {str(e)}')

        return redirect('plugins:netpicker:mappeddevice_list')
