# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2025 Michael Pucher <contact@cluo.sh>
from __future__ import annotations
import os
import zmq
from enum import Enum
from dataclasses import dataclass
from typing import Mapping, Optional, Iterator, Any, Sequence, Tuple
from .common import ManageRequest, ManageStatus, PipelineNodeType, \
    PipelineNodeExtraArgs


REOXIDE_MANAGE_HOST = os.environ.get(
    'REOXIDE_MANAGE_HOST',
    'ipc:///tmp/reoxide-manage.sock'
)
REOXIDE_MANAGE_BIND = os.environ.get(
    'REOXIDE_MANAGE_BIND',
    'ipc:///tmp/reoxide-manage.sock'
)


class MessageErrorCode(Enum):
    ExpectedSeparator = 0
    NonUtf8String = 1
    UnexpectedMessageEnd = 2
    ReceiveError = 3
    UnexpectedNodeTag = 4
    ActionExpectedGotRule = 5
    GotActionInPool = 6
    UnexpectedArgTag = 7
    UnexpectedArgType = 8
    MissingPipelineName = 9
    NonExistantPipeline = 10
    PipelineAlreadyExists = 11
    ErrorWhileWritingPipeline = 12
    CouldNotDeletePipeline = 13
    CannotDeleteCurrent = 14

    def __bytes__(self):
        return bytes([self.value])

    def raise_ex(self):
        raise MessageError(self)


class MessageError(Exception):
    error: MessageErrorCode

    def __init__(self, error: MessageErrorCode):
        super().__init__(error.name)
        self.error = error


class PipelineYamlError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class SerializeIDError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


@dataclass
class Plugin:
    name: str
    actions: dict[str, int]
    rules: dict[str, int]

    def serialize(self) -> list[bytes]:
        return [self.name.encode()] \
            + [a.encode() for a in self.actions] + [b''] \
            + [r.encode() for r in self.rules] + [b'']


@dataclass
class PipelineBaseNode:
    TYPENAME = 'Base'
    parent: Optional[PipelineBaseAction]
    name: str

    def serialize_as_yaml(self, level: int = 0) -> list[str]:
        raise NotImplemented

    def serialize(self) -> list[bytes]:
        raise NotImplemented

    def serialize_with_ids(
        self,
        plugins: Mapping[str, Tuple[int, Plugin]]
    ) -> list[bytes]:
        raise NotImplemented

    def resolve_plugin_names(self, plugins: Sequence[Plugin]) -> None:
        raise NotImplemented


@dataclass
class PipelineActionRule:
    group_name: str
    plugin: Optional[str]


@dataclass
class PipelineBaseAction(PipelineBaseNode):
    def serialize(self) -> list[bytes]:
        return []


@dataclass
class PipelineAction(PipelineBaseAction, PipelineActionRule):
    TYPENAME = 'Action'
    extra_args: list[Any]

    def serialize_as_yaml(self, level: int = 0) -> list[str]:
        indent = '  ' * level

        out = [
            f'{indent}- action: {self.name}',
            f'{indent}  group: {self.group_name}'
        ]

        if self.extra_args:
            out.append(f'{indent}  extra_args:')
            indent += '    '
            for arg in self.extra_args:
                if isinstance(arg, bool):
                    out.extend([
                        f'{indent}- type: bool',
                        f'{indent}  value: {"true" if arg else "false"}'
                    ])
                else:
                    assert False, "Unsupported extra arg"

        return out 

    def serialize(self) -> list[bytes]:
        if self.extra_args:
            return [
                PipelineNodeType.ActionWithArgs.value,
                self.name.encode(),
                self.group_name.encode(),
                self.plugin.encode() if self.plugin else b''
            ] + serialize_extra_args(self.extra_args)
        else:
            return [
                PipelineNodeType.Action.value,
                self.name.encode(),
                self.group_name.encode(),
                self.plugin.encode() if self.plugin else b''
            ]

    def serialize_with_ids(
        self,
        plugins: Mapping[str, Tuple[int, Plugin]]
    ) -> list[bytes]:
        if not self.plugin:
            msg = f'Action "{self.name}" has no plugin assigned'
            raise SerializeIDError(msg)

        plugin_info = plugins.get(self.plugin)
        if plugin_info is None:
            msg = f'Action "{self.name}" uses unknown/unloaded '
            msg += f'plugin "{self.plugin}"'
            raise SerializeIDError(msg)

        plugin_id, plugin = plugin_info
        action_id = plugin.actions.get(self.name)
        if action_id is None:
            msg = f'Action "{self.name}" is not part of '
            msg += f'plugin "{self.plugin}"'
            raise SerializeIDError(msg)

        if not self.group_name:
            msg = f'Action "{self.name}" has no group assigned'
            raise SerializeIDError(msg)

        arg_count = len(self.extra_args)
        msg = [
            PipelineNodeType.Action.value,
            plugin_id.to_bytes(2, 'little'),
            action_id.to_bytes(2, 'little'),
            self.group_name.encode(),
            arg_count.to_bytes()
        ]

        for arg in self.extra_args:
            if isinstance(arg, bool):
                msg += [
                    PipelineNodeExtraArgs.Bool.value,
                    arg.to_bytes()
                ]
            else:
                assert False, "Unsupported extra arg"

        return msg

    def resolve_plugin_names(self, plugins: Sequence[Plugin]):
        for plugin in plugins:
            if self.name in plugin.actions:
                self.plugin = plugin.name


def serialize_extra_args(args: list[Any]) -> list[bytes]:
    arg_bytes = []

    for arg in args:
        if isinstance(arg, bool):
            arg_bytes += [
                PipelineNodeExtraArgs.Bool.value,
                b'\x01' if arg else b''
            ]
        else:
            assert False, "Unsupported extra arg"

    return arg_bytes + [b'']


@dataclass
class PipelinePool(PipelineBaseAction):
    TYPENAME = 'Pool'
    rules: list[PipelineRule]

    def serialize_as_yaml(self, level: int = 0) -> list[str]:
        indent = '  ' * level

        out = [
            f'{indent}- pool: {self.name}',
            f'{indent}  rules:'
        ]

        for rule in self.rules:
            out.extend(rule.serialize_as_yaml(level + 1))

        return out 

    def serialize(self) -> list[bytes]:
        return [
            PipelineNodeType.Pool.value,
            self.name.encode()
        ] + [
            part
            for rule in self.rules
            for part in rule.serialize()
        ] + [b'']

    def serialize_with_ids(
        self,
        plugins: Mapping[str, Tuple[int, Plugin]]
    ) -> list[bytes]:
        return [
            PipelineNodeType.Pool.value,
            self.name.encode()
        ] + [
            s
            for serialized in [
                r.serialize_with_ids(plugins)
                for r in self.rules
            ]
            for s in serialized
        ] + [b'e']

    def resolve_plugin_names(self, plugins: Sequence[Plugin]):
        for rule in self.rules:
            rule.resolve_plugin_names(plugins)


@dataclass
class PipelineRule(PipelineBaseNode, PipelineActionRule):
    TYPENAME = 'Rule'

    def serialize_as_yaml(self, level: int = 0) -> list[str]:
        indent = '  ' * level
        out =  [
            f'{indent}- rule: {self.name}',
        ]
        if self.name != 'PROC_SPEC_RULES':
            out.append(f'{indent}  group: {self.group_name}')
        return out

    def serialize(self) -> list[bytes]:
        return [
            PipelineNodeType.Rule.value,
            self.name.encode(),
            self.group_name.encode(),
            self.plugin.encode() if self.plugin else b''
        ]

    def serialize_with_ids(
        self,
        plugins: Mapping[str, Tuple[int, Plugin]]
    ) -> list[bytes]:
        if self.name == 'PROC_SPEC_RULES':
            # TODO: We don't have a way to implement this atm
            return []

        if not self.plugin:
            msg = f'Rule "{self.name}" has no plugin assigned'
            raise SerializeIDError(msg)

        plugin_info = plugins.get(self.plugin)
        if plugin_info is None:
            msg = f'Rule "{self.name}" uses unknown/unloaded '
            msg += f'plugin "{self.plugin}"'
            raise SerializeIDError(msg)

        plugin_id, plugin = plugin_info
        rule_id = plugin.rules.get(self.name)
        if rule_id is None:
            msg = f'Rule "{self.name}" is not part of '
            msg += f'plugin "{self.plugin}"'
            raise SerializeIDError(msg)

        if not self.group_name:
            msg = f'Rule "{self.name}" has no group assigned'
            raise SerializeIDError(msg)

        return [
            PipelineNodeType.Rule.value,
            plugin_id.to_bytes(2, 'little'),
            rule_id.to_bytes(2, 'little'),
            self.group_name.encode(),
            b'\x00'
        ]

    def resolve_plugin_names(self, plugins: Sequence[Plugin]):
        for plugin in plugins:
            if self.name in plugin.rules:
                self.plugin = plugin.name


@dataclass
class PipelineGroup(PipelineBaseAction):
    TYPENAME = 'Group'
    actions: list[PipelineBaseAction]

    def serialize_as_yaml(self, level: int = 0) -> list[str]:
        indent = '  ' * level

        out = [
            f'{indent}- action_group: {self.name}',
            f'{indent}  actions:'
        ]

        for action in self.actions:
            out.extend(action.serialize_as_yaml(level + 1))

        return out 

    def serialize(self) -> list[bytes]:
        return [
            PipelineNodeType.Group.value,
            self.name.encode()
        ] + [
            part
            for action in self.actions
            for part in action.serialize()
        ] + [b'']

    def serialize_with_ids(
        self,
        plugins: Mapping[str, Tuple[int, Plugin]]
    ) -> list[bytes]:
        return [
            PipelineNodeType.Group.value,
            self.name.encode()
        ] + [
            s
            for serialized in [
                a.serialize_with_ids(plugins)
                for a in self.actions
            ]
            for s in serialized
        ] + [b'e']

    def resolve_plugin_names(self, plugins: Sequence[Plugin]):
        for action in self.actions:
            action.resolve_plugin_names(plugins)


class ManageClient:
    ctx: zmq.Context
    sock: zmq.Socket

    def __init__(self, url=REOXIDE_MANAGE_HOST):
        self._init_zmq(url)

    def _init_zmq(self, url: str):
        self.ctx = zmq.Context()

        # Management port for managing the manager
        self.sock = self.ctx.socket(zmq.REQ)
        self.sock.connect(url)

        self.poller = zmq.Poller()
        self.poller.register(self.sock, zmq.POLLIN)

    def list_plugins(self) -> list[Plugin]:
        self.sock.send(bytes(ManageRequest.ListPlugins))

        socks = dict(self.poller.poll(3000))
        if self.sock not in socks:
            raise TimeoutError()

        msg_bytes = self.sock.recv_multipart()
        plugins = []

        try:
            status = ManageStatus(msg_bytes[0][0])
        except ValueError:
            status = ManageStatus.UnknownStatus

        match status:
            case ManageStatus.Ok:
                try:
                    msg_iter = iter(msg_bytes[1:])
                    plugins = parse_plugins(msg_iter)
                except UnicodeDecodeError:
                    MessageErrorCode.NonUtf8String.raise_ex()
                except StopIteration:
                    MessageErrorCode.UnexpectedMessageEnd.raise_ex()
            case _:
                MessageErrorCode.ReceiveError.raise_ex()

        return plugins

    def fetch_pipeline(self, name: str) -> PipelineGroup:
        self.sock.send_multipart([
            bytes(ManageRequest.FetchPipeline),
            name.encode()
        ])

        socks = dict(self.poller.poll(3000))
        if self.sock not in socks:
            raise TimeoutError()

        msg_bytes = self.sock.recv_multipart()
        root = PipelineGroup(None, "universal", [])

        try:
            status = ManageStatus(msg_bytes[0][0])
        except ValueError:
            status = ManageStatus.UnknownStatus

        match status:
            case ManageStatus.Ok:
                try:
                    msg_iter = iter(msg_bytes[1:])
                    root.actions = parse_actions(root, msg_iter)
                except UnicodeDecodeError:
                    MessageErrorCode.NonUtf8String.raise_ex()
                except StopIteration:
                    MessageErrorCode.UnexpectedMessageEnd.raise_ex()
            case _:
                MessageErrorCode.ReceiveError.raise_ex()

        return root

    def apply_pipeline(self, pipeline: PipelineGroup) -> Optional[str]:
        msg = [bytes(ManageRequest.ApplyPipeline)]
        msg.extend(pipeline.serialize())
        self.sock.send_multipart(msg)

        socks = dict(self.poller.poll(3000))
        if self.sock not in socks:
            raise TimeoutError()

        msg_bytes = self.sock.recv_multipart()
        try:
            status = ManageStatus(msg_bytes[0][0])
        except ValueError:
            status = ManageStatus.UnknownStatus

        match status:
            case ManageStatus.Ok:
                return None
            case ManageStatus.PipelineMessageError:
                try:
                    return MessageErrorCode(msg_bytes[1][0]).name
                except ValueError:
                    return "Unknown internal error"
            case ManageStatus.PipelineSerializationError:
                return msg_bytes[1].decode()
            case _:
                return 'Unknown error while applying pipeline'

    def save_pipeline(
        self,
        name: str,
        pipeline: PipelineGroup
    ) -> Optional[str]:
        msg = [bytes(ManageRequest.SavePipeline), name.encode()]
        msg.extend(pipeline.serialize())
        self.sock.send_multipart(msg)

        socks = dict(self.poller.poll(3000))
        if self.sock not in socks:
            raise TimeoutError()

        msg_bytes = self.sock.recv_multipart()
        try:
            status = ManageStatus(msg_bytes[0][0])
        except ValueError:
            status = ManageStatus.UnknownStatus

        match status:
            case ManageStatus.Ok:
                return None
            case ManageStatus.PipelineMessageError:
                try:
                    return MessageErrorCode(msg_bytes[1][0]).name
                except ValueError:
                    return "Unknown internal error"
            case ManageStatus.PipelineSerializationError:
                return msg_bytes[1].decode()
            case _:
                return 'Unknown error while saving pipeline'

    def delete_pipeline(
        self,
        name: str,
    ) -> Optional[str]:
        msg = [bytes(ManageRequest.DeletePipeline), name.encode()]
        self.sock.send_multipart(msg)

        socks = dict(self.poller.poll(3000))
        if self.sock not in socks:
            raise TimeoutError()

        msg_bytes = self.sock.recv_multipart()
        try:
            status = ManageStatus(msg_bytes[0][0])
        except ValueError:
            status = ManageStatus.UnknownStatus

        match status:
            case ManageStatus.Ok:
                return None
            case ManageStatus.PipelineMessageError:
                try:
                    return MessageErrorCode(msg_bytes[1][0]).name
                except ValueError:
                    return "Unknown internal error"
            case _:
                return 'Unknown error while deleting pipeline'

    def list_pipelines(self) -> list[str]:
        self.sock.send(bytes(ManageRequest.ListPipelines))

        socks = dict(self.poller.poll(3000))
        if self.sock not in socks:
            raise TimeoutError()

        msg_bytes = self.sock.recv_multipart()
        try:
            status = ManageStatus(msg_bytes[0][0])
        except ValueError:
            status = ManageStatus.UnknownStatus

        match status:
            case ManageStatus.Ok:
                try:
                    return [
                        pipeline.decode()
                        for pipeline in msg_bytes[1:]
                    ]
                except UnicodeDecodeError:
                    MessageErrorCode.NonUtf8String.raise_ex()
                except StopIteration:
                    MessageErrorCode.UnexpectedMessageEnd.raise_ex()
            case _:
                MessageErrorCode.ReceiveError.raise_ex()


def parse_plugins(stream: Iterator[bytes]) -> list[Plugin]:
    plugins = []

    while name_bytes := next(stream, None):
        name = name_bytes.decode()

        actions = {}
        idx = 0
        for action in stream:
            if action == b'':
                break
            actions[action.decode()] = idx
            idx += 1

        rules = {}
        idx = 0
        for rule in stream:
            if rule == b'':
                break
            rules[rule.decode()] = idx
            idx += 1

        plugins.append(Plugin(name, actions, rules))

    return plugins


def parse_rules(
    parent: PipelinePool,
    stream: Iterator[bytes]
) -> list[PipelineRule]:
    rules = []

    while tag_byte := next(stream, None):
        try:
            tag = PipelineNodeType(tag_byte)
        except ValueError:
            MessageErrorCode.UnexpectedNodeTag.raise_ex()

        if tag != PipelineNodeType.Rule:
            MessageErrorCode.GotActionInPool.raise_ex()

        name = next(stream).decode()
        group_name = next(stream).decode()
        plugin_name = next(stream).decode()
        if not plugin_name:
            plugin_name = None

        rules.append(PipelineRule(
            parent=parent,
            name=name,
            group_name=group_name,
            plugin=plugin_name
        ))

    return rules


def parse_extra_args(
    stream: Iterator[bytes]
) -> list[Any]:
    extra_args = []

    while tag_bytes := next(stream, None):
        try:
            tag = PipelineNodeExtraArgs(tag_bytes)
        except ValueError:
            MessageErrorCode.UnexpectedArgTag.raise_ex()

        match tag:
            case PipelineNodeExtraArgs.Bool:
                val = next(stream)
                if val:
                    extra_args.append(True)
                else:
                    extra_args.append(False)

    return extra_args


def parse_action(
    parent: Optional[PipelineBaseAction],
    stream: Iterator[bytes]
) -> PipelineAction:
    name = next(stream).decode()
    group_name = next(stream).decode()
    plugin_name = next(stream).decode()
    if not plugin_name:
        plugin_name = None

    return PipelineAction(
        parent=parent,
        name=name,
        group_name=group_name,
        plugin=plugin_name,
        extra_args=[]
    )


def parse_action_with_args(
    parent: Optional[PipelineBaseAction],
    stream: Iterator[bytes]
) -> PipelineAction:
    name = next(stream).decode()
    group_name = next(stream).decode()
    plugin_name = next(stream).decode()
    if not plugin_name:
        plugin_name = None

    return PipelineAction(
        parent=parent,
        name=name,
        group_name=group_name,
        plugin=plugin_name,
        extra_args=parse_extra_args(stream)
    )


def parse_group(
    parent: Optional[PipelineGroup],
    stream: Iterator[bytes]
) -> PipelineGroup:
    name = next(stream).decode()
    action = PipelineGroup(parent, name, [])
    action.actions = parse_actions(action, stream)
    return action


def parse_pool(
    parent: Optional[PipelineGroup],
    stream: Iterator[bytes]
) -> PipelinePool:
    name = next(stream).decode()
    action = PipelinePool(parent, name, [])
    action.rules = parse_rules(action, stream)
    return action


def parse_actions(
    parent: Optional[PipelineGroup],
    stream: Iterator[bytes]
) -> list[PipelineBaseAction]:
    actions = []

    while tag_bytes := next(stream, None):
        try:
            tag = PipelineNodeType(tag_bytes)
        except ValueError:
            MessageErrorCode.UnexpectedNodeTag.raise_ex()

        match tag:
            case PipelineNodeType.Action:
                actions.append(parse_action(parent, stream))
            case PipelineNodeType.ActionWithArgs:
                actions.append(parse_action_with_args(parent, stream))
            case PipelineNodeType.Group:
                actions.append(parse_group(parent, stream))
            case PipelineNodeType.Pool:
                actions.append(parse_pool(parent, stream))
            case PipelineNodeType.Rule:
                MessageErrorCode.ActionExpectedGotRule.raise_ex()

    return actions

def parse_yaml_actions(
    parent: PipelineBaseAction,
    yaml_nodes: list[dict[str, Any]]
) -> list[PipelineBaseAction]:
    actions = []

    for item in yaml_nodes:
        if 'action' in item and 'extra_args' in item:
            if 'group' not in item:
                msg = f'Missing group name in item: {item}'
                raise PipelineYamlError(msg)
            if not isinstance(item['extra_args'], list):
                msg = f'Extra args must be list: {item}'
                raise PipelineYamlError(msg)

            extra_args = []
            for arg in item['extra_args']:
                if 'type' not in arg:
                    msg = f'Extra arg missing type: {arg}'
                    raise PipelineYamlError(msg)
                if 'value' not in arg:
                    msg = f'Extra arg missing value: {arg}'
                    raise PipelineYamlError(msg)

                if arg['type'] != 'bool':
                    msg = f'Only boolean extra args supported: {arg}'
                    raise PipelineYamlError(msg)
                if not isinstance(arg['value'], bool):
                    msg = f'Value is not boolean: {arg}'
                    raise PipelineYamlError(msg)
                extra_args.append(arg['value'])

            actions.append(PipelineAction(
                name=item['action'],
                group_name=item['group'],
                plugin=None,
                extra_args=extra_args,
                parent=parent
            ))
        elif 'action' in item:
            if 'group' not in item:
                msg = f'Missing group name in item: {item}'
                raise PipelineYamlError(msg)

            actions.append(PipelineAction(
                name=item['action'],
                group_name=item['group'],
                plugin=None,
                extra_args=[],
                parent=parent
            ))
        elif 'action_group' in item:
            if 'actions' not in item:
                msg = f'Missing actions list in group: {item}'
                raise PipelineYamlError(msg)

            group_actions = item['actions']
            if not isinstance(group_actions, list):
                msg = f'Actions in group are not a list: '
                msg += str(group_actions)
                raise PipelineYamlError(msg)

            group = PipelineGroup(
                name=item['action_group'],
                actions=[],
                parent=parent
            )
            group.actions = parse_yaml_actions(group, group_actions)
            actions.append(group)
        elif 'pool' in item:
            if 'rules' not in item:
                msg = f'Missing actions list in group: {item}'
                raise PipelineYamlError(msg)

            rules = item['rules']
            if not isinstance(rules, list):
                msg = f'Rules in pule are not a list: {rules}'
                raise PipelineYamlError(msg)

            pool = PipelinePool(
                name=item['pool'],
                rules=[],
                parent=parent
            )

            for rule in rules:
                if 'rule' not in rule:
                    msg = f'Rule missing "rule" name: {rule}'
                    raise PipelineYamlError(msg)

                group_name = ''
                if 'group' in rule:
                    group_name = rule['group']
                elif rule['rule'] == 'PROC_SPEC_RULES':
                    # Special case! Ignore for now
                    pass
                else:
                    msg = f'Missing group name in rule: {rule}'
                    raise PipelineYamlError(msg)

                pool.rules.append(PipelineRule(
                    name=rule['rule'],
                    group_name=group_name,
                    plugin=None,
                    parent=pool
                ))

            actions.append(pool)
        else:
            msg = 'Yaml node not valid in this location: '
            msg += str(item)
            raise PipelineYamlError(msg)

    return actions
