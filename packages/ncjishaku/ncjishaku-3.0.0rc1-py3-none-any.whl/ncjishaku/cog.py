# -*- coding: utf-8 -*-

"""
ncjishaku.cog
~~~~~~~~~~~~

The Jishaku debugging and diagnostics cog implementation.

:copyright: (c) 2021 Devon (scarletcafe) R
:copyright: (c) 2025 CrystalAlpha358
:license: MIT, see LICENSE for more details.

"""

import inspect
import typing

from nextcord.ext import commands

from ncjishaku.features.baseclass import Feature
from ncjishaku.features.filesystem import FilesystemFeature
from ncjishaku.features.guild import GuildFeature
from ncjishaku.features.invocation import InvocationFeature
from ncjishaku.features.management import ManagementFeature
from ncjishaku.features.python import PythonFeature
from ncjishaku.features.root_command import RootCommand
from ncjishaku.features.shell import ShellFeature
from ncjishaku.features.sql import SQLFeature
from ncjishaku.features.voice import VoiceFeature

__all__ = (
    "Jishaku",
    "STANDARD_FEATURES",
    "OPTIONAL_FEATURES",
    "setup",
)

STANDARD_FEATURES = (VoiceFeature, GuildFeature, FilesystemFeature, InvocationFeature, ShellFeature, SQLFeature, PythonFeature, ManagementFeature, RootCommand)

OPTIONAL_FEATURES: typing.List[typing.Type[Feature]] = []


class Jishaku(*OPTIONAL_FEATURES, *STANDARD_FEATURES):  # type: ignore  # pylint: disable=too-few-public-methods
    """
    The frontend subclass that mixes in to form the final Jishaku cog.
    """


async def async_setup(bot: commands.Bot):
    """
    The async setup function defining the ncjishaku.cog and ncjishaku extensions.
    """

    await bot.add_cog(Jishaku(bot=bot))  # type: ignore


def setup(bot: commands.Bot):  # pylint: disable=inconsistent-return-statements
    """
    The setup function defining the ncjishaku.cog and ncjishaku extensions.
    """

    if inspect.iscoroutinefunction(bot.add_cog):
        return async_setup(bot)

    bot.add_cog(Jishaku(bot=bot))  # type: ignore[reportUnusedCoroutine]
