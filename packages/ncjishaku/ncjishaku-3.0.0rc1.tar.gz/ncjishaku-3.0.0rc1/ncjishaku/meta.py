# -*- coding: utf-8 -*-

"""
ncjishaku.meta
~~~~~~~~~~~~

Meta information about ncjishaku.

:copyright: (c) 2021 Devon (scarletcafe) R
:copyright: (c) 2025 CrystalAlpha358
:license: MIT, see LICENSE for more details.

"""

import importlib.metadata
import re
import typing

__all__ = (
    '__author__',
    '__copyright__',
    '__docformat__',
    '__license__',
    '__title__',
    '__version__',
    'version_info'
)

_VERSION_PATTERN: typing.Final = r"""
    ^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<micro>\d+)
    (?:(?P<level>a|b|rc)(?P<serial>\d+))?
    (?:\.post(?P<post>\d+))?
    (?:\.dev(?P<dev>\d+))?
"""


class VersionInfo(typing.NamedTuple):
    """Version info named tuple for Jishaku"""
    major: int
    minor: int
    micro: int
    releaselevel: str
    serial: int

    @classmethod
    def parse_version(cls, version: str) -> typing.Self:
        m = re.match(_VERSION_PATTERN, version, re.VERBOSE | re.IGNORECASE)
        if not m:
            raise ValueError('Failed to parse version')

        match m['level']:
            case 'a':
                releaselevel = 'alpha'
            case 'b':
                releaselevel = 'beta'
            case 'rc':
                releaselevel = 'preview'
            case _:
                releaselevel = 'final'

        return cls(int(m['major']), int(m['minor']), int(m['micro']), releaselevel, int(m['serial'] or 0))


__author__ = 'CrystalAlpha358'
__copyright__ = 'Copyright (c) 2025 CrystalAlpha358'
__docformat__ = 'restructuredtext en'
__license__ = 'MIT'
__title__ = 'ncjishaku'
try:
    __version__ = importlib.metadata.version(__title__)
except importlib.metadata.PackageNotFoundError:
    __version__ = '0.0.0'

version_info = VersionInfo.parse_version(__version__)
