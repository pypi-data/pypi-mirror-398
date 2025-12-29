# -*- coding: utf-8 -*-

"""
ncjishaku subclassing test 1
~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a valid extension file for nextcord intended to
discover weird behaviors related to subclassing.

This variant overrides behavior using a Feature.

:copyright: (c) 2021 Devon (scarletcafe) R
:copyright: (c) 2025 CrystalAlpha358
:license: MIT, see LICENSE for more details.

"""

from nextcord.ext import commands

import ncjishaku
from ncjishaku.types import ContextT


class ThirdPartyFeature(ncjishaku.Feature):
    """
    overriding feature for test
    """

    @ncjishaku.Feature.Command(name="jishaku", aliases=["jsk"], invoke_without_command=True, ignore_extra=False)
    async def jsk(self, ctx: ContextT):
        """
        override test
        """
        return await ctx.send("The behavior of this command has been overridden with a third party feature.")


class Magnet1(ThirdPartyFeature, *ncjishaku.OPTIONAL_FEATURES, *ncjishaku.STANDARD_FEATURES):  # pylint: disable=too-few-public-methods
    """
    The extended Jishaku cog
    """


def setup(bot: commands.Bot):
    """
    The setup function for the extended cog
    """

    bot.add_cog(Magnet1(bot=bot))
