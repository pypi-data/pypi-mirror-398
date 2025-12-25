import re

from fastapi import Request

from amsdal_server.apps.common.serializers.fields_restriction import FieldsRestriction
from amsdal_server.apps.common.serializers.filter import Filter
from amsdal_server.apps.common.serializers.filter import FilterType

FILTER_TYPE_RE = '|'.join(list(FilterType.__members__.keys()))
RESTIRCTION_FILTER_RE = re.compile(r'fields\[(?P<class_name>.*)\]')
FILTER_RE = re.compile(rf'filter\[(?P<filter_name>.+?)(__(?P<filter_type>{FILTER_TYPE_RE}))?\]')

KEY_REGEX = re.compile(r'^[\w$]+$')


def get_fields_restrictions(request: Request) -> dict[str, FieldsRestriction]:
    restrictions: dict[str, FieldsRestriction] = {}

    for k, v in request.query_params.items():
        if (match := RESTIRCTION_FILTER_RE.match(k)) and (class_name := match.group('class_name')):
            restrictions[class_name] = FieldsRestriction(class_name=class_name, fields=v.split(','))

    return restrictions


def get_filters(request: Request) -> list[Filter]:
    filters: list[Filter] = []

    for k, v in request.query_params.items():
        if (match := FILTER_RE.match(k)) and (filter_name := match.group('filter_name')):
            if not v:
                continue

            if not KEY_REGEX.match(filter_name):
                msg = f'Invalid key: {filter_name}'
                raise ValueError(msg)

            filters.append(
                Filter(
                    key=filter_name,
                    filter_type=FilterType[match.group('filter_type') or 'eq'],
                    target=v,
                ),
            )

    return filters
