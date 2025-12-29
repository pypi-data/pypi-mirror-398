# -*- coding: utf-8 -*-

"""
ncjishaku.repl
~~~~~~~~~~~~

Repl-related operations and tools for Jishaku.

:copyright: (c) 2021 Devon (scarletcafe) R
:copyright: (c) 2025 CrystalAlpha358
:license: MIT, see LICENSE for more details.

"""

from ncjishaku.repl.compilation import *  # noqa: F403
from ncjishaku.repl.disassembly import create_tree, disassemble, get_adaptive_spans  # type: ignore  # noqa: F401
from ncjishaku.repl.inspections import all_inspections  # type: ignore  # noqa: F401
from ncjishaku.repl.repl_builtins import get_var_dict_from_ctx  # type: ignore  # noqa: F401
from ncjishaku.repl.scope import *  # noqa: F403
