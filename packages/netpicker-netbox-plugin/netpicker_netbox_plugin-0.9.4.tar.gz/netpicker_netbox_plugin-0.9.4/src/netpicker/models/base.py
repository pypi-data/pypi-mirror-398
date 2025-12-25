from copy import deepcopy
from operator import attrgetter

from django.db import models

from netbox.models import BookmarksMixin, CloningMixin, CustomFieldsMixin, CustomLinksMixin, CustomValidationMixin, \
    ExportTemplatesMixin
from utilities.querysets import RestrictedQuerySet


class ProxyQuerySet(RestrictedQuerySet):
    def __init__(self, *args, data: list = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = self._result_cache = data or []

    def _clone(self):
        r = super()._clone()
        r.data = r._result_cache = deepcopy(self.data)
        r.model = self.model
        return r

    def all(self):
        result = type(self)(model=self.model, data=deepcopy(self.data))
        return result

    def order_by(self, *fields):
        r = super()._clone()
        # cheating a little
        if fields:
            reverse = fields[0][0] == '-'
            if reverse:
                fields = (fields[0][1:], *fields[1:])
            r.data = r._result_cache = sorted(self.data, key=attrgetter(*fields), reverse=reverse)
        return r

    def iterator(self, chunk_size=None):
        return iter(self.data)

    def exists(self):
        return True

    def __bool__(self):
        return bool(self.data)

    def __str__(self):
        return f"{type(self).__name__}: model={self.model} data={self.data}"


def get_attr(self, *, field: str = None):
    return self.record[field]


class NetpickerModel(
    BookmarksMixin,
    CloningMixin,
    CustomFieldsMixin,
    CustomLinksMixin,
    CustomValidationMixin,
    ExportTemplatesMixin,
    models.Model
):
    class Meta:
        abstract = True

    @classmethod
    def from_basemodel(cls, basemodel):
        fields = {f.attname for f in cls._meta.fields}
        kwargs = {k: getattr(basemodel, k) for k in basemodel.model_fields if k in fields}
        if 'id' in kwargs:
            kwargs['pk'] = kwargs.get('id')
        return cls(**kwargs)

    @classmethod
    def from_dict(cls, attrs):
        fields = {f.attname for f in cls._meta.fields}
        kwargs = {k: v for k, v in attrs.items() if k in fields}
        if 'id' in kwargs:
            kwargs['pk'] = kwargs.get('id')
        return cls(**kwargs)
