# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2025 Michael Pucher <contact@cluo.sh>
from __future__ import annotations
import ctypes
import _ctypes
import sys
from pathlib import Path
from typing import Optional
from .manage import client
from .config import log 


class _ActionDefinition(ctypes.Structure):
    _fields_ = [
        ('name', ctypes.c_char_p),
        ('cnstr', ctypes.POINTER(ctypes.c_ubyte))
    ]

class _RuleDefinition(ctypes.Structure):
    _fields_ = [
        ('name', ctypes.c_char_p),
        ('cnstr', ctypes.POINTER(ctypes.c_ubyte))
    ]

class _CActionDefinition(ctypes.Structure):
    _fields_ = [
        ('name', ctypes.c_char_p),
        ('cnstr', ctypes.POINTER(ctypes.c_ubyte)),
        ('destroy', ctypes.POINTER(ctypes.c_ubyte)),
        ('apply', ctypes.POINTER(ctypes.c_ubyte))
    ]

class _CRuleDefinition(ctypes.Structure):
    _fields_ = [
        ('name', ctypes.c_char_p),
        ('cnstr', ctypes.POINTER(ctypes.c_ubyte)),
        ('destroy', ctypes.POINTER(ctypes.c_ubyte)),
        ('oplist', ctypes.POINTER(ctypes.c_ubyte)),
        ('apply', ctypes.POINTER(ctypes.c_ubyte))
    ]


class Plugin(client.Plugin):
    file_path: Path

    def __init__(
        self,
        file_path: Path,
        actions: dict[str, int],
        rules: dict[str, int]
    ):
        self.actions = actions
        self.rules = rules
        self.name = file_path.stem.strip('lib')
        self.file_path = file_path

    @staticmethod
    def load_shared_lib(file: Path) -> Optional[Plugin]:
        path = file.resolve()
        log.info(f'Loading {path}')

        # Python currently doesn't have a platform independent way to
        # unload CDLLs after loading them... this is gonna be rough
        # if we want to rebuild the plugins dynamically
        lib = ctypes.CDLL(str(path))

        try:
            getattr(lib, 'reoxide_c_abi')
            c_abi = True
        except AttributeError:
            c_abi = False

        try:
            getattr(lib, 'reoxide_rule_defs')
            getattr(lib, 'reoxide_rule_count')
        except AttributeError:
            log.error(f'Library {file} does not contain rule definitions')
            return None

        try:
            getattr(lib, 'reoxide_action_defs')
            getattr(lib, 'reoxide_action_count')
        except AttributeError:
            log.error(f'Library {file} does not contain action definitions')
            return None

        try:
            getattr(lib, 'reoxide_plugin_new')
            getattr(lib, 'reoxide_plugin_delete')
        except AttributeError:
            log.error(f'Library {file} does not contain context functions')
            return None

        action_count = ctypes.c_size_t.in_dll(lib, 'reoxide_action_count').value
        action_def = _CActionDefinition if c_abi else _ActionDefinition
        action_table = (action_def * action_count)
        actions = {
            action.name.decode(): i
            for i, action 
            in enumerate(action_table.in_dll(lib, "reoxide_action_defs"))
        }

        rule_count = ctypes.c_size_t.in_dll(lib, 'reoxide_rule_count').value
        rule_def = _CRuleDefinition if c_abi else _RuleDefinition
        rule_table = (rule_def * rule_count)
        rule = {
            rule.name.decode(): i
            for i, rule
            in enumerate(rule_table.in_dll(lib, "reoxide_rule_defs"))
        }

        # We do not actually need the plugin anymore in the manager.
        # Technically we do not even need to load it, but there does
        # not seem to be a lightweight parser for shared libraries.
        # It is also worth nothing that this will not unload shared
        # libraries that have been loaded in response to loading the
        # original library! But it should allow us to hot reload
        # plugin files if we want it.
        if sys.platform == "linux":
            handle = lib._handle
            _ctypes.dlclose(handle)

        return Plugin(path, actions, rule)
