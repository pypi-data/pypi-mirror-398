import importlib
import os
import re
import sys

from pathlib import Path


def _exit(msg):
    print(msg)
    sys.exit(1)


plugin_name = sys.modules[__name__].__package__.split('.')[0]

target_package = "netbox"
djs = f"{target_package}.configuration"
re_plugins = re.compile(r'(?P<prolog>^.*?)\[\s*?(?P<plugins>[^]]*?)](?P<epilog>.*)$', re.MULTILINE | re.DOTALL)


def post_install(dockerized):
    nb_hack = 'DEBUG="true" SECRET_KEY="dummyKeyWithMinimumLength-------------------------"'
    if dockerized:
        cmd = f"{nb_hack} /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py collectstatic --no-input"
    else:
        home = Path(sys.modules[djs].__file__).parent.parent
        cmd = rf"""cd {home} \
                    && {nb_hack} python manage.py migrate {plugin_name} \
                    && {nb_hack} python manage.py collectstatic --noinput """

    xc = os.system(cmd)
    return xc == 0


def install_for_netbox():
    """ Modify the target package configuration after installation """
    # 1. check if netbox is installed
    try:
        from django.core.exceptions import ImproperlyConfigured
    except ImportError:
        return _exit('No netbox package installed (in the current environment)')

    nbconf = f"{target_package}.configuration"
    try:
        netbox_config = importlib.import_module(nbconf)
    except ImportError:
        return _exit('No netbox package installed (in the current environment)')
    if dockerized := hasattr(netbox_config, 'read_configurations'):
        config_file = Path('/etc/netbox/config/plugins.py')
    else:
        try:
            djs = f"{target_package}.settings"
            nb_settings = importlib.import_module(djs)
            os.environ["DJANGO_SETTINGS_MODULE"] = djs
        except ImportError:
            return _exit('No netbox package installed (in the current environment)')
        except ImproperlyConfigured:
            return _exit('Current netbox configuration is invalid (or cannot be loaded)')

        package_path = Path(nb_settings.__file__).parent
        # Locate configuration file
        config_file = package_path / "configuration.py"
        if not config_file.exists():
            return _exit('This netbox installation has not been configured (yet).')

        try:
            netbox_config = importlib.import_module(f"{target_package}.configuration")
        except ImportError:
            return _exit('This netbox installation has no valid configuration.')

    plugins = getattr(netbox_config, 'PLUGINS', None)
    if plugins and plugin_name in plugins:
        return _exit(f'Plugin `{plugin_name}` is already installed.')

    if sys.stdin.isatty():
        go = input('Do you want to install this netbox plugin? [y/N]: ')
        if go != 'y':
            return _exit(f'Plugin `{plugin_name}` not installed')
    elif '--no-input' not in sys.argv:
        return _exit(f'Plugin `{plugin_name}` cannot be installed unattended without --no-input option.')
    config_py = original_config = config_file.read_text()
    if plugins is None:
        config_py += f"\nPLUGINS = [{repr(plugin_name)}]\n"
    else:
        parts = re.split(r'(?P<assigning>PLUGINS\s*=\s*)', config_py, re.MULTILINE)
        assert len(parts) > 1
        last_plugins = parts[-1]
        if m := re.search(re_plugins, last_plugins):
            prolog = m.groupdict()['prolog']
            epilog = m.groupdict()['epilog']
            plugins_array = m.groupdict()['plugins']
            glue = ', ' if plugins_array else ''
            plugins_array += f'{glue}"netpicker"'
            parts[-1] = f"{prolog}[{plugins_array}]{epilog}"
        config_py = "".join(parts)
    config_file.write_text(config_py)
    try:
        importlib.reload(netbox_config)
    except ImportError:
        config_file.write_text(original_config)
        return _exit('Failed to install netbox plugin')

    if post_install(dockerized):
        print(f'Plugin `{plugin_name}` installed successfully.')
        return 0
    return _exit('Plugin installation failed')


if __name__ == "__main__":
    install_for_netbox()
