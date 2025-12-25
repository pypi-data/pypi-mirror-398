import inspect
import json
import re
import typing
from functools import partial
from textwrap import indent
from typing import Any, Callable

from django.core.cache import cache
from django.template import Context
from django.template.base import Template
from django.utils.safestring import mark_safe
from netpicker_client import ApiClient, AutomationApi, BodyExecuteJobApiV1AutomationTenantExecutePost, \
    BodyStoreJobApiV1AutomationTenantJobPost, Configuration, \
    DevicesApi, JobListItem

from dcim.models import Device
from netpicker.models import Backup, BackupSearchHit, Job, MappedDevice, NetpickerSetting

PY_INIT = '__init__.py'
SIMPLE_JOB_TPL = """from comfy.automate import job


@job({% if platforms %}
    platform={{ platforms }},{% endif %}
    tags='netboxed'
)
def {{ name }}(device{% if variables %}, {{ variables }}{% endif %}):
    device.cli.send_config_set([
{{ commands }}
    ])
"""


def netpicker_settings(require: bool = True) -> NetpickerSetting | None:
    settings = NetpickerSetting.objects.first()
    if settings is None and require:
        raise ValueError("Settings for netpicker plugin not set")
    return settings


def get_client():
    settings = NetpickerSetting.objects.first()
    configuration = Configuration(access_token=settings.api_key, host=settings.server_url,
                                  server_variables={'tenant': settings.tenant})
    cli = ApiClient(configuration=configuration)
    return cli


def automation_api():
    return AutomationApi(get_client())


def devices_api():
    return DevicesApi(get_client())


def render_simple_job(job):
    variables = set()

    def render_cmd_str(raw: str):
        var = re.findall(r'\{([a-zA-Z_]\w*)}??', raw)
        variables.update(var)
        prefix = 'f' if var else ''
        return prefix + repr(raw)

    cmds = ',\n'.join(map(render_cmd_str, job.commands))

    context = dict(
        name=mark_safe(job.name),
        platforms=mark_safe(repr(sorted(list(job.platforms)))) if job.platforms else None,
        commands=mark_safe(indent(cmds, ' ' * 8)),
        variables=mark_safe(', '.join(sorted(variables))),
    )
    template = Template(SIMPLE_JOB_TPL)
    ctx = Context(context)
    py_source = template.render(ctx)
    return py_source


re_commands = re.compile(r'device\.cli\.send_config_set\s*\(\s*\[\s*(?P<cfg>[^]]*?)]', re.DOTALL | re.MULTILINE)


def extract_commands(sources: dict[str, str]) -> list[str] | None:
    src = sources.get(PY_INIT)
    if src:
        if m := re.search(re_commands, src):
            cfg = m.groupdict()['cfg'].rstrip('\n, ')
            raw = cfg.split('\n')
            result = [c.strip().lstrip('f').strip(''','" ''') for c in raw]
            return result
    return None


T = typing.TypeVar('T')


class Fetcher(typing.Protocol[T]):
    def __call__(self) -> T:
        ...


class PageFetcher(typing.Protocol[T]):
    def __call__(self, size: int, page: int | None) -> list[T]:
        ...


class Selector(typing.Protocol[T]):
    def __call__(self, item: T) -> bool:
        ...


def api_cache(cache_key: str, cache_ttl: int = None):
    def outer(func):
        def inner(*args, **kwargs):
            if cache_key is not None and (result := cache.get(cache_key)):
                return result
            result = func(*args, **kwargs)
            if cache_key is not None:
                cache.set(cache_key, result, timeout=cache_ttl)
            return result
        return inner

    outer.pop = partial(cache.delete, cache_key)
    return outer


def greedy_reader(
        fetcher: PageFetcher[T] | Fetcher[T],
        transformer: Callable[[T], Any] | None = None,
        selector: Selector | None = None,
        max_pages: int | None = None,
) -> list[Any]:
    sf = inspect.signature(fetcher)
    if {'page', 'size'} <= sf.parameters.keys():
        # Iterate all pages reliably (assumes API page indexing is 1-based)
        result = []
        page = 1
        pages_limit = max_pages
        while True:
            data = fetcher(size=100, page=page)
            selected = [n for n in data.items if selector(n)] if selector else data.items
            items = [transformer(n) for n in selected] if transformer else selected
            result.extend(items)

            # Stop if we've reached the last page or hit the optional max_pages limit
            if data.page >= data.pages:
                break
            if pages_limit is not None and page >= pages_limit:
                break
            page += 1
    else:
        data = fetcher()
        selected = [n for n in data if selector(n)] if selector else data
        result = [transformer(n) for n in selected] if transformer else selected
    return result


def get_domains(cache_ttl: int | None = 6000):
    cli = get_client()
    devices_api = DevicesApi(cli)
    tenant = cli.configuration.server_variables['tenant']
    cacher = api_cache(f"{tenant}/domains", cache_ttl)
    result = cacher(devices_api.domains)(tenant=tenant)
    return result


def get_netpicker_devices():
    api = devices_api()
    tenant = api.api_client.configuration.server_variables['tenant']
    fetcher = partial(api.list, tenant=tenant)
    cacher = api_cache(f"{tenant}/devices", 300)
    data = cacher(greedy_reader)(fetcher, lambda n: (n.ipaddress, n.platform, tenant, n.name))
    return data


def get_device_readouts(device_id: int, ipaddress: str):
    def to_backup(obj):
        result = Backup.from_basemodel(obj)
        result.pk = f"{ipaddress}-{obj.id}"
        result.ipaddress = ipaddress
        result.device_id = device_id
        result.upload_date = obj.upload_date.replace(microsecond=0)
        return result

    api = devices_api()
    tenant = api.api_client.configuration.server_variables['tenant']
    fetcher = partial(api.list_configurations, tenant=tenant, ipaddress=ipaddress)
    cacher = api_cache(f"netpicker/{tenant}/{ipaddress}/backups", 600)
    result = cacher(greedy_reader)(fetcher, to_backup)  # , f"netpicker/{tenant}/{ipaddress}/backups")
    return result


def get_readout_history(ipaddress: str, after: str = None):
    api = devices_api()
    tenant = api.api_client.configuration.server_variables['tenant']
    after_key = after if after else "all"
    cacher = api_cache(f"netpicker/{tenant}/{ipaddress}/history/{after_key}", 600)
    cached_ep = cacher(api.backup_history_api_v1_devices_tenant_ipaddress_config_history_get)
    data = cached_ep(tenant=tenant, ipaddress=ipaddress, after=after)
    return [n | dict(deltas=f"{n['insertions']}/{n['deletions']}", ipaddress=ipaddress) for n in data]


def download_config(ipaddress: str, config_id: str):
    api = devices_api()
    tenant = api.api_client.configuration.server_variables['tenant']
    cacher = api_cache(f"{tenant}/{ipaddress}/{config_id}/backup", None)
    result = cacher(api.get_configuration)(tenant=tenant, ipaddress=ipaddress, config_id=config_id, preview=True)
    return result


def get_job_logs(job_name: str | None = None):
    api = automation_api()
    tenant = api.api_client.configuration.server_variables['tenant']
    end_point = api.get_joblog_report_api_v1_automation_tenant_logs_get
    fetcher = partial(end_point, tenant=tenant, ordering=['-created'], job_name=job_name)
    cacher = api_cache(f"{tenant}/{job_name}/logs", 30)
    data = cacher(greedy_reader)(fetcher, max_pages=5)
    return data


def get_job_log_details(id: str):
    api = automation_api()
    tenant = api.api_client.configuration.server_variables['tenant']
    obj = api.get_joblog_by_id_api_v1_automation_tenant_logs_id_get(tenant=tenant, id=id)
    return obj


def job_transformer(raw: JobListItem):
    kw = raw.model_dump()
    platforms = kw.get('platforms') or kw.get('platform')
    kw['platforms'] = sorted(set(platforms)) if platforms else []
    kw.pop('platform', None)
    kw.update(id=kw['name'])
    result = Job.from_dict(kw)
    return result


def get_jobs():
    api = automation_api()
    tenant = api.api_client.configuration.server_variables['tenant']

    def safe_fetcher():
        """Fetcher that fixes None platforms in raw response before deserialization"""
        response = api.list_jobs_api_v1_automation_tenant_job_get_without_preload_content(tenant=tenant)

        response_data = response.data
        if isinstance(response_data, bytes):
            data = json.loads(response_data.decode('utf-8'))
        elif isinstance(response_data, str):
            data = json.loads(response_data)
        else:
            data = response_data

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    if 'platform' in item and 'platforms' not in item:
                        item['platforms'] = item.pop('platform')
                    if item.get('platforms') is None:
                        item['platforms'] = []
        elif isinstance(data, dict):
            if 'items' in data:
                for item in data['items']:
                    if isinstance(item, dict):
                        if 'platform' in item and 'platforms' not in item:
                            item['platforms'] = item.pop('platform')
                        if item.get('platforms') is None:
                            item['platforms'] = []

        from netpicker_client.models.job_list_item import JobListItem
        if isinstance(data, list):
            return [JobListItem.from_dict(item) for item in data]
        elif isinstance(data, dict) and 'items' in data:
            fixed_items = [JobListItem.from_dict(item) for item in data['items']]

            class Response:
                def __init__(self, items):
                    self.items = items
                    self.page = data.get('page', 1)
                    self.pages = data.get('pages', 1)
            return Response(fixed_items)
        else:
            return []

    fetcher = safe_fetcher
    cacher = api_cache(f"{tenant}/jobs", 600)
    result = cacher(greedy_reader)(fetcher, transformer=job_transformer)
    return result


def get_job_details(name: str):
    api = automation_api()
    tenant = api.api_client.configuration.server_variables['tenant']
    cacher = api_cache(f"{tenant}/{name}/job", 600)
    info = cacher(api.get_job_api_v1_automation_tenant_job_name_get)(tenant=tenant, name=name)
    main_job = info.jobs[0]
    kw = {k: getattr(main_job, k) for k in main_job.model_fields} | dict(source=info.sources)
    platforms = sum((n.platform for n in info.jobs), [])
    kw['id'] = kw['name']
    kw['platforms'] = sorted(platforms)
    kw['commands'] = extract_commands(info.sources)
    result = Job.from_dict(kw)
    return result


def save_job(job: Job):
    api = automation_api()
    tenant = api.api_client.configuration.server_variables['tenant']
    source = render_simple_job(job)
    sources = {PY_INIT: source}
    post = BodyStoreJobApiV1AutomationTenantJobPost(name=job.name, sources=sources)
    api.store_job_api_v1_automation_tenant_job_post(tenant, post)
    api_cache(f"{tenant}/{job.name}/job").pop()
    api_cache(f"{tenant}/jobs").pop()


def delete_job(job: Job):
    api = automation_api()
    tenant = api.api_client.configuration.server_variables['tenant']
    api.delete_job_api_v1_automation_tenant_job_name_delete(tenant, job.name)
    api_cache(f"{tenant}/{job.name}/logs").pop()
    api_cache(f"{tenant}/{job.name}/job").pop()
    api_cache(f"{tenant}/jobs").pop()


def run_job(
    job: Job,
    devices: list[Device] | None = None,
    ip_addresses: list[str] | None = None,
    variables: dict[str, str] = None
):
    from netpicker.utilities import get_device_ip

    api = automation_api()
    tenant = api.api_client.configuration.server_variables['tenant']

    ips = []
    if devices:
        device_ips = [get_device_ip(dev) for dev in devices if get_device_ip(dev)]
        ips.extend(device_ips)
    if ip_addresses:
        ips.extend(ip_addresses)

    ips = list(dict.fromkeys(ips)) if ips else None

    msg = BodyExecuteJobApiV1AutomationTenantExecutePost(
        name=job.name, devices=ips, sources=None, variables=variables or {}
    )
    api.execute_job_api_v1_automation_tenant_execute_post(tenant, msg)
    api_cache(f"{tenant}/{job.name}/logs").pop()


@api_cache('fixtures', 3600)
def get_fixtures():
    api = automation_api()
    tenant = api.api_client.configuration.server_variables['tenant']
    result = api.list_fixtures_api_v1_automation_tenant_fixtures_get(tenant=tenant)
    return result


def search_configs(q: str):
    qs = MappedDevice.objects.values_list('ipaddress', 'netbox_id', 'name').all()
    known_ips = dict((ip, info) for ip, *info in qs)
    # known_ips = dict(MappedDevice.objects.values_list('ipaddress', 'netbox_id').all())

    def get_hits():
        try:
            data = api.search_configs_api_v1_devices_tenant_search_configs_get(tenant=tenant, search_string=q)
            return data['results']
        except Exception:
            # Return empty results on API error instead of raising exception
            return []

    def select(n):
        # ipaddress = n['device']['ipaddress']
        # selected = known_ips.get(ipaddress, [None])[0] is not None
        # return selected
        return True

    def extract(n):
        ipaddress = n['device']['ipaddress']
        kw = dict(ipaddress=ipaddress, matches=n['matches'], **dict(zip(('device_id', 'name'), known_ips[ipaddress])))
        return BackupSearchHit.from_dict(kw)

    try:
        api = devices_api()
        tenant = api.api_client.configuration.server_variables['tenant']
        cacher = api_cache(f"{tenant}/search_configs/{q}", 300)
        result = cacher(greedy_reader)(get_hits, extract, select)
        return result
    except Exception:
        # Return empty results on any error instead of raising exception
        return []


def search_configs_with_error_handling(q: str):
    """
    Search configs and return a tuple of (results, error_occurred)
    """
    try:
        results = search_configs(q)
        return results, False
    except Exception:
        return [], True


def search_jobs_with_error_handling(q: str):
    """
    Search jobs and return a tuple of (results, error_occurred)
    Filters jobs client-side by name, author, platforms, or tags
    """
    try:
        all_jobs = get_jobs()
        q_lower = q.lower()
        filtered_jobs = []
        for job in all_jobs:
            if q_lower in job.name.lower():
                filtered_jobs.append(job)
                continue
            if hasattr(job, 'author') and job.author and q_lower in job.author.lower():
                filtered_jobs.append(job)
                continue
            if hasattr(job, 'platforms') and job.platforms:
                if any(q_lower in str(platform).lower() for platform in job.platforms):
                    filtered_jobs.append(job)
                    continue
            if hasattr(job, 'tags') and job.tags:
                if any(q_lower in str(tag).lower() for tag in job.tags):
                    filtered_jobs.append(job)
                    continue
        return filtered_jobs, False
    except Exception:
        return [], True
