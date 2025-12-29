# -*- coding: utf-8 -*-

"""
ncjishaku.types
~~~~~~~~~~~~~

Declarations for type checking

:copyright: (c) 2021 Devon (scarletcafe) R
:copyright: (c) 2025 CrystalAlpha358
:license: MIT, see LICENSE for more details.

"""

import typing

from nextcord.ext import commands

BotT = typing.Union[commands.Bot, commands.AutoShardedBot]
ContextT = typing.TypeVar('ContextT', commands.Context[commands.Bot], commands.Context[commands.AutoShardedBot])
ContextA = commands.Context[BotT]
