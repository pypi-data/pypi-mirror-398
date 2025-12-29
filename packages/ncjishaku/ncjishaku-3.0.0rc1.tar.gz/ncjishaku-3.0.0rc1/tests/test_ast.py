# -*- coding: utf-8 -*-

"""
ncjishaku ast tree generation test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2022 Devon (scarletcafe) R
:copyright: (c) 2025 CrystalAlpha358
:license: MIT, see LICENSE for more details.

"""

import inspect

from ncjishaku.repl.disassembly import create_tree


def test_ast_missing_fields():
    # should not raise
    create_tree(inspect.cleandoc("""
        def h(*, a):
            print(a)
    """), use_ansi=False)
