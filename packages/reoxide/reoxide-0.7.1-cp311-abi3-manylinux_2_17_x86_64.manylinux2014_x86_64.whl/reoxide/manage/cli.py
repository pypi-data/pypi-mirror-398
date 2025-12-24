# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2025 Michael Pucher <contact@cluo.sh>
from .client import ManageClient


def cmd_list_actions(**kwargs):
    url = kwargs.get('manage_host')
    assert url
    c = ManageClient(url)
    plugins = c.list_plugins()
    plugins.sort(key=lambda p: p.name)

    actions = [(p.name, a) for p in plugins for a in p.actions]
    for plugin_name, action in actions:
        print(f'{plugin_name}: {action}')


def cmd_list_rules(**kwargs):
    url = kwargs.get('manage_host')
    assert url
    c = ManageClient(url)
    plugins = c.list_plugins()
    plugins.sort(key=lambda p: p.name)

    rules = [(p.name, r) for p in plugins for r in p.rules]
    for plugin_name, rule in rules:
        print(f'{plugin_name}: {rule}')
