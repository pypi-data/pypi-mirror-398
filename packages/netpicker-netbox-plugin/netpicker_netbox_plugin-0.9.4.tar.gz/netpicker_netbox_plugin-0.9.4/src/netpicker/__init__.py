from django.template import Context, Template
from django.utils.safestring import SafeText

from netbox.plugins import PluginConfig, get_plugin_config


logo_b64 = ('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjI2IiBoZWlna'
            'HQ9IjY4MSIgdmlld0JveD0iMCAwIDYyNiA2ODEiIGZpbGw9Im5vbmUiIHhtbG5zPS'
            'JodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0zMTMgNjI1Ljg'
            '5QzQ4NS43MTYgNjI1Ljg5IDYyNS43MyA0ODUuODc2IDYyNS43MyAzMTMuMTZDNjI1'
            'LjczIDE0MC40NDQgNDg1LjcxNiAwLjQyOTk5MyAzMTMgMC40Mjk5OTNDMTQwLjI4N'
            'CAwLjQyOTk5MyAwLjI3MDAyIDE0MC40NDQgMC4yNzAwMiAzMTMuMTZDMC4yNzAwMi'
            'A0ODUuODc2IDE0MC4yODQgNjI1Ljg5IDMxMyA2MjUuODlaIiBmaWxsPSIjRkFEODd'
            'BIi8+CjxwYXRoIGQ9Ik01NTUuNjIgMjU3LjhDNjA1LjEyIDMwNy4zIDYwNS4xMiAz'
            'ODguMTggNTU1LjYyIDQzNy42OEwzMTMgNjgwLjNMNzAuMzggNDM3LjY4QzIwLjg4I'
            'DM4OC4xOCAyMC44OCAzMDcuMyA3MC4zOCAyNTcuOEwzMTMgMTUuMThMNTU1LjYyID'
            'I1Ny44WiIgZmlsbD0iIzY5M0IyRiIvPgo8cGF0aCBkPSJNNDY0LjA5IDQ3NC44QzQ'
            'zMi4wMyA0NzQuNCA0MDAuMDggNDYyLjAzIDM3NS43NCA0MzcuNjhMMzEzIDM3NC45'
            'NEwyNTAuMjcgNDM3LjY4QzIyNS45MiA0NjIuMDMgMTkzLjk3IDQ3NC40IDE2MS45M'
            'iA0NzQuOEwzMTMuMDEgNjI1Ljg5TDQ2NC4xIDQ3NC44SDQ2NC4wOVoiIGZpbGw9Ii'
            'NGQUQ4N0EiLz4KPHBhdGggZD0iTTQ2NC4wOSA0NzQuOEM0MzIuMDMgNDc0LjQgNDA'
            'wLjA4IDQ2Mi4wMyAzNzUuNzQgNDM3LjY4TDMxMyAzNzQuOTRWNjI1Ljg4TDQ2NC4w'
            'OSA0NzQuNzlWNDc0LjhaIiBmaWxsPSIjRjhDMTczIi8+CjxwYXRoIGQ9Ik0zNzUuO'
            'DEgMjU3LjczQzQwMC4xNiAyMzMuNDUgNDMyIDIyMS4wOCA0NjQuMDkgMjIwLjY4TD'
            'MxMyA2OS41OUwxNjEuOTEgMjIwLjY4QzE5NC4xOCAyMjEuMDggMjI1Ljc0IDIzMy4'
            '0NSAyNTAuMjYgMjU3LjhMMzEyLjk5IDMyMC41NEwzNzUuOCAyNTcuNzRMMzc1Ljgx'
            'IDI1Ny43M1oiIGZpbGw9IiNEMTNDMzEiLz4KPHBhdGggZD0iTTQwMi45OCAyODQuO'
            'TdDMzY4LjI5IDMxOS42NiAzNjguMjkgMzc1LjgzIDQwMi45NCA0MTAuNDhDNDM3Lj'
            'QxIDQ0NC45NSA0OTMuOTQgNDQ0Ljk1IDUyOC40MSA0MTAuNDhDNTYyLjg4IDM3Ni4'
            'wMSA1NjIuODggMzE5LjQ4IDUyOC40MSAyODUuMDFDNDkzLjk1IDI1MC41NSA0Mzcu'
            'NDYgMjUwLjU0IDQwMi45OCAyODQuOTdaIiBmaWxsPSJ3aGl0ZSIvPgo8cGF0aCBkP'
            'SJNOTcuNTkgNDEwLjQ4QzEzMi4wNiA0NDQuOTUgMTg4LjU5IDQ0NC45NSAyMjMuMD'
            'YgNDEwLjQ4QzI1Ny43MiAzNzUuODIgMjU3LjcxIDMxOS42NCAyMjMuMDIgMjg0Ljk'
            '3QzE4OC41NyAyNTAuNTQgMTMyLjA1IDI1MC41NCA5Ny41OSAyODUuMDFDNjMuMTMg'
            'MzE5LjQ4IDYzLjEyIDM3Ni4wMSA5Ny41OSA0MTAuNDhaIiBmaWxsPSJ3aGl0ZSIvP'
            'go8cGF0aCBkPSJNMTYwLjMzIDQxMy40M0MxOTYuNjEgNDEzLjQzIDIyNi4wMiAzOD'
            'QuMDIgMjI2LjAyIDM0Ny43NEMyMjYuMDIgMzExLjQ2IDE5Ni42MSAyODIuMDUgMTY'
            'wLjMzIDI4Mi4wNUMxMjQuMDUgMjgyLjA1IDk0LjY0IDMxMS40NiA5NC42NCAzNDcu'
            'NzRDOTQuNjQgMzg0LjAyIDEyNC4wNSA0MTMuNDMgMTYwLjMzIDQxMy40M1oiIGZpb'
            'Gw9IiM2OTNCMkYiLz4KPHBhdGggZD0iTTQ2NS42OCA0MTMuNDNDNTAxLjk2IDQxMy'
            '40MyA1MzEuMzcgMzg0LjAyIDUzMS4zNyAzNDcuNzRDNTMxLjM3IDMxMS40NiA1MDE'
            'uOTYgMjgyLjA1IDQ2NS42OCAyODIuMDVDNDI5LjQgMjgyLjA1IDM5OS45OSAzMTEu'
            'NDYgMzk5Ljk5IDM0Ny43NEMzOTkuOTkgMzg0LjAyIDQyOS40IDQxMy40MyA0NjUuN'
            'jggNDEzLjQzWiIgZmlsbD0iIzY5M0IyRiIvPgo8cGF0aCBkPSJNMTIzIDMxNS4xNE'
            'MxMzAuNTcyIDMxNS4xNCAxMzYuNzEgMzA5LjAwMiAxMzYuNzEgMzAxLjQzQzEzNi4'
            '3MSAyOTMuODU4IDEzMC41NzIgMjg3LjcyIDEyMyAyODcuNzJDMTE1LjQyOCAyODcu'
            'NzIgMTA5LjI5IDI5My44NTggMTA5LjI5IDMwMS40M0MxMDkuMjkgMzA5LjAwMiAxM'
            'TUuNDI4IDMxNS4xNCAxMjMgMzE1LjE0WiIgZmlsbD0id2hpdGUiLz4KPHBhdGggZD'
            '0iTTQyOC4zNSAzMTUuMTRDNDM1LjkyMiAzMTUuMTQgNDQyLjA2IDMwOS4wMDIgNDQ'
            'yLjA2IDMwMS40M0M0NDIuMDYgMjkzLjg1OCA0MzUuOTIyIDI4Ny43MiA0MjguMzUg'
            'Mjg3LjcyQzQyMC43NzggMjg3LjcyIDQxNC42NCAyOTMuODU4IDQxNC42NCAzMDEuN'
            'DNDNDE0LjY0IDMwOS4wMDIgNDIwLjc3OCAzMTUuMTQgNDI4LjM1IDMxNS4xNFoiIG'
            'ZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0zMTMgNjkuNTlMMTYxLjkxIDIyMC42OEM'
            'xOTQuMTggMjIxLjA4IDIyNS43NCAyMzMuNDUgMjUwLjI2IDI1Ny44TDMxMi45OSAz'
            'MjAuNTRWNjkuNkwzMTMgNjkuNTlaIiBmaWxsPSIjRUY1NDQwIi8+CjxwYXRoIGQ9I'
            'k0xNjEuOTIgNDc0LjhMMzEzIDYyNS44OUw0NjQuMDkgNDc0LjhMMzEzIDU5NC4zNk'
            'wxNjEuOTIgNDc0LjhaIiBmaWxsPSIjRkZFOUFEIi8+CjxwYXRoIGQ9Ik00NjQuMDk'
            'gMjIwLjY4TDMxMyA2OS41OUwxNjEuOTIgMjIwLjY4TDMxMyA5My4xMUw0NjQuMDkg'
            'MjIwLjY4WiIgZmlsbD0iI0ZBODk3QiIvPgo8cGF0aCBkPSJNMjk0LjU3IDQzNC42O'
            'EMzMDEuODkgNDM2LjY0IDMwNS4yMyA0NDcuODggMzAyLjA0IDQ1OS43OEMyOTguOD'
            'UgNDcxLjY4IDI5MC4zNCA0NzkuNzQgMjgzLjAyIDQ3Ny43OEMyNzUuNyA0NzUuODI'
            'gMjcyLjM2IDQ2NC41OCAyNzUuNTUgNDUyLjY4QzI3OC43NCA0NDAuNzggMjg3LjI1'
            'IDQzMi43MiAyOTQuNTcgNDM0LjY4WiIgZmlsbD0iIzY5M0IyRiIvPgo8cGF0aCBkP'
            'SJNMzMxLjQzIDQzNC42OEMzMjQuMTEgNDM2LjY0IDMyMC43NyA0NDcuODggMzIzLj'
            'k2IDQ1OS43OEMzMjcuMTUgNDcxLjY4IDMzNS42NiA0NzkuNzQgMzQyLjk4IDQ3Ny4'
            '3OEMzNTAuMyA0NzUuODIgMzUzLjY0IDQ2NC41OCAzNTAuNDUgNDUyLjY4QzM0Ny4y'
            'NiA0NDAuNzggMzM4Ljc1IDQzMi43MiAzMzEuNDMgNDM0LjY4WiIgZmlsbD0iIzY5M'
            '0IyRiIvPgo8L3N2Zz4K')


class NetpickerConfig(PluginConfig):
    name = __name__
    verbose_name = "Netpicker Plugin"
    description = "Netpicker Configuration view and Simple Automation"
    version = '0.9.4'
    base_url = "netpicker"

    def logo(self, css_class: str = '', safe: bool = True, **kwargs) -> str:
        if css_class:
            kwargs.setdefault('class', css_class)
        opts = ' '.join((f'{k}="{v}"' for k, v in kwargs.items()))
        tpl = Template(f"""
            {{% load static %}}
            <img src="{logo_b64}" alt="{self.name}" {opts}>""")
        text = tpl.render(Context({}))
        result = SafeText(text) if safe else text
        return result

    def ready(self):
        global netpicker_app
        netpicker_app = self
        from . import signals  # noqa
        from .templatetags import netpicker  # noqa
        super().ready()


config = NetpickerConfig
netpicker_app: NetpickerConfig | None = None


def get_config(cfg):
    return get_plugin_config(get_config.__module__, cfg)
