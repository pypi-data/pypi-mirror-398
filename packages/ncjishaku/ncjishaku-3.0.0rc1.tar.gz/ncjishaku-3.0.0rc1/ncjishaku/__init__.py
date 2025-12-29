# -*- coding: utf-8 -*-

"""
ncjishaku
~~~~~~~

A nextcord extension including useful tools for bot development and debugging.

:copyright: (c) 2024 Devon (scarletcafe) R
:copyright: (c) 2025 CrystalAlpha358
:license: MIT, see LICENSE for more details.

"""

from ncjishaku.cog import Jishaku, STANDARD_FEATURES, OPTIONAL_FEATURES, setup
from ncjishaku.features.baseclass import Feature
from ncjishaku.flags import Flags
from ncjishaku.meta import *  # noqa: F403

__all__ = (
    'Jishaku',
    'Feature',
    'Flags',
    'STANDARD_FEATURES',
    'OPTIONAL_FEATURES',
    'setup',
)
