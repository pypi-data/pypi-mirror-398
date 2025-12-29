# -*- coding: utf-8 -*-

"""
ncjishaku.hljs test
~~~~~~~~~~~~~~~~~

:copyright: (c) 2021 Devon (scarletcafe) R
:copyright: (c) 2025 CrystalAlpha358
:license: MIT, see LICENSE for more details.

"""

import pytest

from ncjishaku.hljs import get_language


@pytest.mark.parametrize(
    ("filename", "language"),
    [
        ('base.py', 'py'),
        ('config.yml', 'yml'),
        ('requirements.txt', ''),
        ('#!/usr/bin/env python', 'python'),
        ('#!/usr/bin/unknown', '')
    ]
)
def test_hljs(filename: str, language: str):
    assert get_language(filename) == language
