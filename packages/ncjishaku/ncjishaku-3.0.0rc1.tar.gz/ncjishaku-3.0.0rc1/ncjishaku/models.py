# -*- coding: utf-8 -*-

"""
ncjishaku.models
~~~~~~~~~~~~~~

Functions for modifying or interfacing with nextcord models.

:copyright: (c) 2021 Devon (scarletcafe) R
:copyright: (c) 2025 CrystalAlpha358
:license: MIT, see LICENSE for more details.

"""

import copy
import typing

import nextcord

from ncjishaku.types import ContextT


async def copy_context_with(
    ctx: ContextT,
    *,
    author: typing.Optional[typing.Union[nextcord.Member, nextcord.User]] = None,
    channel: typing.Optional[nextcord.TextChannel] = None,
    **kwargs: typing.Any
) -> ContextT:
    """
    Makes a new :class:`Context` with changed message properties.
    """

    # copy the message and update the attributes
    alt_message: nextcord.Message = copy.copy(ctx.message)
    alt_message._update(kwargs)  # type: ignore # pylint: disable=protected-access

    if author is not None:
        alt_message.author = author
    if channel is not None:
        alt_message.channel = channel

    # obtain and return a context of the same type
    return await ctx.bot.get_context(alt_message, cls=type(ctx))
