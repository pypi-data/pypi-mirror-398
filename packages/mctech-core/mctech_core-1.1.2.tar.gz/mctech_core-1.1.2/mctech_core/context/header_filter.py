from __future__ import absolute_import
from typing import Dict, List, Literal, Callable

GroupName = Literal['tracingHeaders', 'miscHeaders', 'extrasHeaders']


class PatternFilter:
    group: GroupName
    match: Callable[[str], bool]

    def __init__(self, group: GroupName, match: Callable[[str], bool]):
        self.group = group
        self.match = match


PATTERNS = [
    PatternFilter(
        group='tracingHeaders',
        match=lambda n: n == 'x-request-id' or n == 'x-ot-span-context'
    ),
    PatternFilter(
        group='tracingHeaders',
        match=lambda n: n.startswith('x-b3-')
    ),
    PatternFilter(
        group='miscHeaders',
        match=lambda n: n.startswith('x-forwarded-')
    )]


def process(headers: List[str]):
    result: Dict[GroupName, List[str]] = {
        # string[]
        'tracingHeaders': [],
        # string[]
        'extrasHeaders': [],
        # string[]
        'miscHeaders': []
    }

    # 排除所有不是以'x-'开头的key
    for header in filter(lambda h: h.startswith('x-'), headers):
        # 排除满足$excludes集合中条件的
        pattern = next(filter(lambda p: p.match(header), PATTERNS), None)
        group = pattern.group if pattern else 'extrasHeaders'
        list = result[group]
        list.append(header)
    return result
