from django.utils.functional import lazy
from django.utils.safestring import SafeText

from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem


def lazy_label():
    return SafeText('Netpicker')


imported_device_buttons = [
    PluginMenuButton(
        link='plugins:netpicker:import',
        title='Import',
        icon_class='mdi mdi-netpicker',
    )
]


menu = PluginMenu(
    label=lazy(lazy_label, str),
    groups=(
        (
            'Netpicker', (
                PluginMenuItem(
                    link='plugins:netpicker:mappeddevice_list',
                    link_text='Devices',
                    permissions=["netpicker.view_netpickerautomation"],
                ),
                PluginMenuItem(
                    link='plugins:netpicker:backupsearchhit_list',
                    link_text='Config search',
                    permissions=["netpicker.view_netpickerautomation"],
                ),
                PluginMenuItem(
                    link='plugins:netpicker:job_list',
                    link_text='Automation Jobs',
                    permissions=["netpicker.view_netpickerautomation"],
                ),
                PluginMenuItem(
                    link='plugins:netpicker:log_list',
                    link_text='Automation Logs',
                    permissions=["netpicker.view_netpickerautomation"],
                ),
                PluginMenuItem(
                    link='plugins:netpicker:netpickersetting',
                    link_text='Settings',
                    permissions=["netpicker.view_netpickersetting"],
                ),
            )
        ),
    ),
    icon_class='mdi mdi-bird',
)
