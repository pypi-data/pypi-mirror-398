# -*- coding: utf-8 -*-
#
# pyscreeps_arena - config.py
# Author: 我阅读理解一直可以的
# Template: V0.1
# Versions:
# .2025 01 01 - v0.1:
#   Created.
#
import os
from pyscreeps_arena.core import const
arena = "green"
level = "basic"
season = "beta"
language = 'cn'
# 默认路径: 用户 + ScreepsArena + beta-spawn_and_swamp + main.mjs
target = None
TARGET_GETTER = lambda: os.path.join(os.path.expanduser('~'), 'ScreepsArena', f'{("season" + season) if season.isdigit() else season}-{const.ARENA_NAMES.get(arena, "spawn_and_swamp")}{"-advanced" if level in ["advance", "advanced"] else ""}', 'main.mjs')

