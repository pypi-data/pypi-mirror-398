# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2025 Michael Pucher <contact@cluo.sh>
import argparse
import filecmp
import io
import logging
import os
import shutil
import sys
import threading
import tomllib
import yaml
import zmq
import struct
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional
from .plugin import Plugin
from .config import APP_NAME, APP_AUTHOR, log
from .manage import ManageRequest, ManageStatus
from .manage.client import MessageError, MessageErrorCode, \
    SerializeIDError, parse_actions, parse_yaml_actions, \
    PipelineGroup, REOXIDE_MANAGE_HOST, REOXIDE_MANAGE_BIND
from .manage import cli as manage_cli


REOXIDE_HOST = os.environ.get(
    'REOXIDE_HOST',
    'ipc:///tmp/reoxide.sock'
)
REOXIDE_BIND = os.environ.get(
    'REOXIDE_BIND',
    'ipc:///tmp/reoxide.sock'
)
REOXIDE_CONFIG = os.environ.get('REOXIDE_CONFIG')


class ReOxideError(Exception):
    pass


def ld_library_path() -> Path:
    return Path(__file__).parent.resolve() / 'data' / 'bin'


def ghidra_decomp_path(ghidra_root: Path) -> Optional[Path]:
    p = ghidra_root / 'Ghidra' / 'Features' / 'Decompiler' / 'os'
    p = p / 'linux_x86_64' / 'decompile'
    return p if p.exists() and p.is_file() else None


def config_path_check(path: Path) -> Path:
    if not path.exists():
        exit(f'config: {path} does not exist')
    if not path.is_file():
        exit(f'config: {path} is not a file')
    return path.resolve()


def parse_data_dir(config: dict[str, Any]) -> Optional[Path]:
    if 'data-directory' in config:
        data_dir = Path(config['data-directory'])
        return data_dir.resolve()
    return None


def cmd_init_config(
    config_path: Path,
    data_dir: Path,
    **_
):
    print('Creating new basic config.')
    ghidra_root = input('Enter a Ghidra root install directory: ')
    
    ghidra_root = Path(ghidra_root)
    if not ghidra_root.exists():
        exit('Entered Ghidra root directory does not exist.')
    
    ghidra_decomp = ghidra_decomp_path(ghidra_root)
    if not ghidra_decomp:
        msg = 'Entered Ghidra root does not contain decompiler.'
        msg += f' Tried path: {ghidra_decomp}'
        exit(msg)
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open('w', encoding='utf-8') as f:
        print(f'data-directory = "{data_dir}"', file=f)
        print(file=f)
        print('[[ghidra-install]]', file=f)
        print('enabled = true', file=f)
        print(f'root-dir = "{ghidra_root}"', file=f)
    
    print(f'Config saved to {config_path}')


def cmd_link_ghidra(
    config_path: Path,
    config: dict[str, Any],
    **_
):
    bin_path = Path(__file__).parent.resolve() / 'data' / 'bin'
    reoxide_bin =  bin_path / 'decompile'
    try:
        reoxide_bin = reoxide_bin.resolve(strict=True)
    except OSError:
        exit('Could not resolve path to ReOxide binary')

    if 'ghidra-install' not in config:
        msg = 'No Ghidra installation info (ghidra-install) found in '
        msg += f'{config_path}. Need at least one!'
        exit(msg)

    for ghidra_install in config['ghidra-install']:
        ghidra_root = Path(ghidra_install['root-dir'])
        print(f'Checking Ghidra install at "{ghidra_root}"')

        ghidra_enabled = True
        if 'enabled' in ghidra_install:
            entry = ghidra_install['enabled']
            if not isinstance(entry, bool):
                print(f'WARNING: "enabled" is not a boolean value, skipping "{ghidra_root}"')
                continue

            if not entry:
                ghidra_enabled = False

        ghidra_decomp = ghidra_decomp_path(ghidra_root)
        if not ghidra_decomp:
            print(f'WARNING: No decompiler found for "{ghidra_root}", skipping')
            continue

        if ghidra_enabled:
            print(f'Linking "{ghidra_root}" with ReOxide')

            if ghidra_decomp.is_symlink():
                try:
                    decomp_resolved = ghidra_decomp.resolve(strict=True)
                except OSError:
                    print(f'Could not resolve symlink for "{ghidra_decomp}"')
                    continue

                if decomp_resolved != reoxide_bin:
                    print(f'WARNING: Ghidra directory "{ghidra_root}"' +\
                        'has a decompile symlink that does not point to ReOxide')
                    continue

                print(f'Ghidra directory "{ghidra_root}" already linked')
                continue

            try:
                os.rename(
                    ghidra_decomp,
                    ghidra_decomp.with_name('decompile.orig')
                )
            except OSError:
                print(
                    f'Could not rename {ghidra_decomp}, skipping "{ghidra_root}"',
                    file=sys.stderr
                )
                continue

            try:
                ghidra_decomp.symlink_to(reoxide_bin)
            except OSError:
                print(
                    f'Could not create ReOxide symlink, skipping "{ghidra_root}"',
                    file=sys.stderr
                )
                continue

            print(f'Successfully linked "{ghidra_root}"')
        else:
            print(f'Unlinking "{ghidra_root}" from ReOxide')

            if not ghidra_decomp.is_symlink():
                print(f'Ghidra directory "{ghidra_root}" is not linked')
                continue

            orig_decomp = ghidra_decomp.with_name('decompile.orig')
            if not orig_decomp.exists() or not orig_decomp.is_file():
                print(f'Cannot find original decompile binary')
                continue

            try:
                ghidra_decomp.unlink()
                os.rename(orig_decomp, ghidra_decomp)
            except OSError:
                print(
                    f'Could not restore decompile, skipping "{ghidra_root}"',
                    file=sys.stderr
                )
                continue

            print(f'Successfully unlinked "{ghidra_root}"')


def cmd_install_ghidra(**kwargs):
    dist_scripts = Path(__file__).parent.resolve() / 'ghidra_scripts'
    default_dir = Path.home() / 'ghidra_scripts'
    ghidra_script_dir = input(f'Enter a Ghidra script directory ({default_dir}): ')

    if not ghidra_script_dir:
        ghidra_script_dir = default_dir
    else:
        ghidra_script_dir = Path(ghidra_script_dir)
    
    ghidra_script_dir.mkdir(parents=True, exist_ok=True)
    for script in dist_scripts.glob('*.py'):
        print(f'Installing {script} to {ghidra_script_dir}')
        shutil.copy(script, ghidra_script_dir)


def cmd_print_plugin_dir(**kwargs):
    data_dir = kwargs.get('data_dir')
    assert data_dir
    plugin_dir = data_dir / 'plugins'
    plugin_dir.mkdir(parents=True, exist_ok=True)
    print(plugin_dir.resolve())


def cmd_print_data_dir(**_):
    print(Path(__file__).parent.resolve() / 'data')


def cmd_print_ld_library_path(**_):
    print(ld_library_path())


def client_cli():
    parser = argparse.ArgumentParser()
    parser.description = 'Client program for the ReOxide daemon.'
    parser.add_argument(
        '-c',
        '--config',
        required=False,
        type=Path,
        help='Specifies path for the reoxide.toml config file'
    )

    # Note, for the host arguments, we do NOT want to use the default
    # arguments from argparse, because we want to have the command line
    # arg take precedence over environment variables when provided
    parser.add_argument(
        '-m',
        '--manage-host',
        required=False,
        type=str,
        help='ZMQ address for configuring ReOxide, ' \
            'can also be set with env var REOXIDE_MANAGE_HOST. ' \
            'default: ipc:///tmp/reoxide-manage.sock'
    )
    cmd_parser = parser.add_subparsers(dest="cmd", required=True)

    desc = 'Initialize a ReOxide config file, needed for other commands to function'
    p = cmd_parser.add_parser(
        'init-config',
        description=desc,
        help=desc,
    )

    desc = 'Replace the Ghidra decompile binary with a symlink to ReOxide/restore original decompile binary'
    p = cmd_parser.add_parser(
        'link-ghidra',
        description=desc,
        help=desc,
    )
    p.set_defaults(func=cmd_link_ghidra)

    desc = 'Install ReOxide helper scripts into a Ghidra script directory. ' \
        'Needs PyGhidra and ReOxide installed in the PyGhidra venv.'
    p = cmd_parser.add_parser(
        'install-ghidra-scripts',
        description=desc,
        help=desc,
    )
    p.set_defaults(func=cmd_install_ghidra)

    desc = 'Output the directory used for loading/storing plugins'
    p = cmd_parser.add_parser(
        'print-plugin-dir',
        description=desc,
        help=desc
    )
    p.set_defaults(func=cmd_print_plugin_dir)

    desc = 'Output the directory containing packaged ReOxide data'
    p = cmd_parser.add_parser(
        'print-data-dir',
        description=desc,
        help=desc
    )
    p.set_defaults(func=cmd_print_data_dir)

    desc = 'Print the LD_LIBRARY_PATH that is needed for ReOxide to run'
    p = cmd_parser.add_parser(
        'print-ld-library-path',
        description=desc,
        help=desc
    )
    p.set_defaults(func=cmd_print_ld_library_path)

    desc = 'Print the list of actions implemented by ReOxide plugins'
    p = cmd_parser.add_parser(
        'list-actions',
        description=desc,
        help=desc
    )
    p.set_defaults(func=manage_cli.cmd_list_actions)

    desc = 'Print the list of rules implemented by ReOxide plugins'
    p = cmd_parser.add_parser(
        'list-rules',
        description=desc,
        help=desc
    )
    p.set_defaults(func=manage_cli.cmd_list_rules)

    args = parser.parse_args()

    config_path = args.config
    if not config_path:
        if REOXIDE_CONFIG:
            config_path = Path(REOXIDE_CONFIG)
        else:
            from platformdirs import user_config_path
            config_dir = user_config_path(APP_NAME, APP_AUTHOR)
            config_path = config_dir / 'reoxide.toml'

    if not config_path.exists() or not config_path.is_file():
        if args.cmd == 'init-config':
            from platformdirs import user_data_path
            data_dir = user_data_path(APP_NAME, APP_AUTHOR)
            cmd_init_config(config_path, data_dir)
            exit()
        else:
            exit(f'Config file does not exist: {config_path}')

    config = dict()
    with config_path.open('rb') as f:
        try:
            config = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            exit(f'Could not parse {config_path}: {e}')

    try:
        data_dir = parse_data_dir(config)
        if not data_dir:
            from platformdirs import user_data_path
            data_dir = user_data_path(APP_NAME, APP_AUTHOR)
    except ReOxideError as ex:
        exit(f'Invalid config file: {ex}')

    manage_host = args.manage_host
    if not manage_host:
        manage_host = REOXIDE_MANAGE_HOST

    try:
        args.func(
            config_path=config_path,
            config=config,
            args=args,
            data_dir=data_dir,
            manage_host=manage_host
        )
    except KeyboardInterrupt:
        exit(1)


class ReOxideManager:
    plugins: list[Plugin]
    current_pipeline: PipelineGroup

    def __init__(
        self,
        config_path: Path,
        log_to_buffer=False,
        bind: Optional[str] = None,
        manage_bind: Optional[str] = None
    ):
        self.log_buffer = io.StringIO()
        if log_to_buffer:
            handler = logging.StreamHandler(self.log_buffer)
            if log.root.handlers:
                handler.setFormatter(log.root.handlers[0].formatter)
                handler.setLevel(log.root.handlers[0].level)
            log.addHandler(handler)

        self._ensure_config_exists(config_path)
        data_dir = self._check_config(config_path)

        if not data_dir:
            from platformdirs import user_data_path
            data_dir = user_data_path(APP_NAME, APP_AUTHOR)

        self.bind = bind if bind else REOXIDE_BIND
        self.manage_bind = manage_bind if manage_bind \
            else REOXIDE_MANAGE_BIND

        self._install_data(data_dir)
        self._load_plugins(data_dir)
        self._load_default_actions(data_dir)
        self._init_zmq()
        self.data_dir = data_dir
        self.pipeline_id = 0

    def _install_data(self, data_dir: Path):
        log.info(f'Using data_dir: {data_dir}')
        base = Path(__file__).parent.resolve() / 'data'
        plugin_dir = data_dir / 'plugins'
        plugin_dir.mkdir(parents=True, exist_ok=True)

        current_yaml = data_dir / 'current.yaml'
        if not current_yaml.exists():
            shutil.copy(base / 'default.yaml', current_yaml)

        core_src = base / 'bin' / 'libcore.so'
        core_dst = plugin_dir / 'libcore.so'
        if not core_dst.exists():
            shutil.copy(core_src, core_dst)
        elif not filecmp.cmp(core_src, core_dst):
            log.info('Updating core plugin with new version')
            core_dst.unlink(missing_ok=True)
            shutil.copy(core_src, core_dst)

    def _ensure_config_exists(self, config_path: Path):
        if not config_path.exists():
            msg = f'Config file not found at "{config_path}"'
            raise ReOxideError(msg)

    def _check_config(self, config_path: Path) -> Optional[Path]:
        config = dict()
        with config_path.open('rb') as f:
            try:
                config = tomllib.load(f)
            except tomllib.TOMLDecodeError as e:
                msg = f'Could not parse {config_path}: {e}'
                raise ReOxideError(msg)

        if 'ghidra-install' not in config:
            msg = 'No Ghidra installation info (ghidra-install) found in '
            msg += f'{config_path}. Need at least one!'
            raise ReOxideError(msg)

        for ghidra_install in config['ghidra-install']:
            ghidra_root = Path(ghidra_install['root-dir'])
            ghidra_decomp = ghidra_decomp_path(ghidra_root)
            if not ghidra_decomp:
                log.warning(f'No decompiler found for {ghidra_root}')
                continue

            if not ghidra_decomp.is_symlink():
                msg = f'decompile file is not a symlink. '
                msg += 'If the Ghidra directory has not been linked with '
                msg += 'ReOxide yet, execute "reoxide link-ghidra".'
                log.warning(msg)
                continue

        return parse_data_dir(config)

    def _load_default_actions(self, data_dir: Path):
        """
        :raises yaml.YAMLError: If the default pipeline is not a
                                valid yaml file.
        """
        actions_path = data_dir / 'current.yaml'
        if not actions_path.exists() or not actions_path.is_file():
            raise ReOxideError(f'{actions_path} does not exist')

        with actions_path.open() as f:
            yaml_data = yaml.safe_load(f)

        root = PipelineGroup(name='universal', parent=None, actions=[])
        root.actions = parse_yaml_actions(root, yaml_data)
        root.resolve_plugin_names(self.plugins)
        self.current_pipeline = root 

        # Whenever we update the actions, make sure we can actually
        # serialize them for the C++ side.
        try:
            self._list_pipeline_for_decomp(self.current_pipeline)
        except SerializeIDError as e:
            log.error(f'Cannot serialize pipeline for decomp: {e}')
            exit(1)

    def _load_plugins(self, data_dir: Path):
        plugin_dir = data_dir / 'plugins'
        plugin_dir.mkdir(parents=True, exist_ok=True)

        self.plugins = []
        for plugin in plugin_dir.glob('*.so'):
            if not plugin.is_file():
                log.info(f'Skipping {plugin} in plugin directory...')
                continue

            p = Plugin.load_shared_lib(plugin)
            if p is None:
                log.error(f'Could not load plugin {plugin}')
                continue
            self.plugins.append(p)
        self.plugins.sort(key=lambda p: p.name)

    def _init_zmq(self):
        self.ctx = zmq.Context()

        # Main socket for decompiler instances to connect on
        self.router = self.ctx.socket(zmq.ROUTER)
        self.router.bind(self.bind)

        # Management port for managing the manager
        self.management = self.ctx.socket(zmq.ROUTER)
        self.management.bind(self.manage_bind)

        # In-memory sockets for properly shutting down the manager
        self.shutdown_signal = self.ctx.socket(zmq.PAIR)
        self.shutdown_signal.connect('inproc://shutdown')
        self.shutdown_sink = self.ctx.socket(zmq.PAIR)
        self.shutdown_sink.bind('inproc://shutdown')

        self.poller = zmq.Poller()
        self.poller.register(self.router, zmq.POLLIN)
        self.poller.register(self.management, zmq.POLLIN)
        self.poller.register(self.shutdown_sink, zmq.POLLIN)

    def get_logs(self) -> str:
        for handler in log.handlers:
            handler.flush()
        return self.log_buffer.getvalue()

    def shutdown(self):
        log.handlers.clear()
        self.shutdown_signal.send(b'')

    def _list_pipeline_for_decomp(
        self,
        pipeline: PipelineGroup
    ) -> list[bytes]:
        plugins = {
            plugin.name: (plug_id, plugin)
            for (plug_id, plugin) in enumerate(self.plugins)
        }

        return [
            s
            for serialized in [
                a.serialize_with_ids(plugins)
                for a in pipeline.actions
            ]
            for s in serialized
        ]

    def _list_plugins(self) -> list[bytes]:
        return [
            s
            for serialized in [p.serialize() for p in self.plugins]
            for s in serialized
        ]

    def _fetch_pipeline(self, args: list[bytes]) -> list[bytes]:
        try:
            if len(args) == 0:
                MessageErrorCode.MissingPipelineName.raise_ex()
            name = args[0].decode()
        except UnicodeDecodeError:
            MessageErrorCode.NonUtf8String.raise_ex()

        if name == 'current':
            pipeline = self.current_pipeline.actions
        else:
            if name == 'default':
                base = Path(__file__).parent.resolve() / 'data'
                pipeline_files = [base / 'default.yaml']
            else:
                pipeline_files = list(self.data_dir.glob(f'{name}.y*ml'))

            if pipeline_files:
                # TODO: Exceptions
                with pipeline_files[0].open() as f:
                    yaml_data = yaml.safe_load(f)

                root = PipelineGroup(
                    name='universal',
                    parent=None,
                    actions=[]
                )
                root.actions = parse_yaml_actions(root, yaml_data)
                root.resolve_plugin_names(self.plugins)
                pipeline = root.actions
            else:
                MessageErrorCode.NonExistantPipeline.raise_ex()

        return [
            s
            for serialized in [
                a.serialize()
                for a in pipeline
            ]
            for s in serialized
        ]

    def _list_pipelines(self) -> list[bytes]:
        return [
            pipeline.stem.encode()
            for pipeline in self.data_dir.glob('*.y*ml')
            if pipeline.is_file() and pipeline.stem != 'default'
        ]

    def _save_pipeline(self, args: list[bytes]) -> list[bytes]:
        try:
            if len(args) == 0:
                MessageErrorCode.MissingPipelineName.raise_ex()
            name = args[0].decode()
        except UnicodeDecodeError:
            MessageErrorCode.NonUtf8String.raise_ex()

        existing_pipelines = list(self.data_dir.glob(f'{name}.y*ml'))
        if existing_pipelines:
            MessageErrorCode.PipelineAlreadyExists.raise_ex()

        actions = parse_actions(None, iter(args[1:]))
        if len(actions) != 1:
            MessageErrorCode.UnexpectedNodeTag.raise_ex()

        root = actions[0]
        if not isinstance(root, PipelineGroup):
            MessageErrorCode.UnexpectedNodeTag.raise_ex()

        self._save_pipeline_file(root, name)
        return self._list_pipelines()

    def _save_pipeline_file(
        self,
        pipeline: PipelineGroup,
        name: str
    ):
        out_file = (self.data_dir / name).with_suffix('.yaml')
        yaml_lines = []
        for action in pipeline.actions:
            yaml_lines.extend(action.serialize_as_yaml())
        yaml = '\n'.join(yaml_lines)

        try:
            with out_file.open('w') as f:
                f.write(yaml)
        except OSError:
            MessageErrorCode.ErrorWhileWritingPipeline.raise_ex()

        log.info(f'Saved pipeline "{name}"')

    def _delete_pipeline(self, args: list[bytes]) -> list[bytes]:
        try:
            if len(args) == 0:
                MessageErrorCode.MissingPipelineName.raise_ex()
            name = args[0].decode()
        except UnicodeDecodeError:
            MessageErrorCode.NonUtf8String.raise_ex()

        if name == 'current' or name == 'default':
            MessageErrorCode.CannotDeleteCurrent.raise_ex()

        existing_pipelines = list(self.data_dir.glob(f'{name}.y*ml'))
        for pipeline in existing_pipelines:
            try:
                pipeline.unlink()
                log.info(f'Deleted pipeline {pipeline.stem}')
            except OSError:
                MessageErrorCode.CouldNotDeletePipeline.raise_ex()

        return self._list_pipelines()

    def _manage(self):
        msg_parts = self.management.recv_multipart()
        client_id = msg_parts[0]
        data = msg_parts[3:]
        msg = [client_id, b'']

        try:
            req_type = ManageRequest(msg_parts[2][0])
        except ValueError:
            req_type = ManageRequest.Unknown

        match req_type:
            case ManageRequest.ListPlugins:
                msg.append(bytes(ManageStatus.Ok))
                msg.extend(self._list_plugins())
            case ManageRequest.FetchPipeline:
                try:
                    pipeline_bytes = self._fetch_pipeline(data)
                    msg.append(bytes(ManageStatus.Ok))
                    msg.extend(pipeline_bytes)
                except MessageError as ec:
                    c = bytes(ManageStatus.PipelineFetchError)
                    msg.append(c)
                    msg.append(bytes(ec.error))
            case ManageRequest.ApplyPipeline:
                try:
                    actions = parse_actions(None, iter(data))
                    if len(actions) != 1:
                        MessageErrorCode.UnexpectedNodeTag.raise_ex()

                    root = actions[0]
                    if not isinstance(root, PipelineGroup):
                        MessageErrorCode.UnexpectedNodeTag.raise_ex()

                    self._list_pipeline_for_decomp(root)
                    self.current_pipeline = root
                    self._save_pipeline_file(root, 'current')
                    self.pipeline_id += 1
                    msg.append(bytes(ManageStatus.Ok))
                    log.info('New pipeline applied')
                except MessageError as ec:
                    c = bytes(ManageStatus.PipelineMessageError)
                    msg.append(c)
                    msg.append(bytes(ec.error))
                    log.error(f'Rejected pipeline: {ec.error}')
                except SerializeIDError as ex:
                    c = bytes(ManageStatus.PipelineSerializationError)
                    msg.append(c)
                    msg.append(str(ex).encode())
                    log.error(f'Rejected pipeline: {ex}')
            case ManageRequest.SavePipeline:
                try:
                    pipeline_list = self._save_pipeline(data)
                    msg.append(bytes(ManageStatus.Ok))
                    msg.extend(pipeline_list)
                except MessageError as ec:
                    c = bytes(ManageStatus.PipelineMessageError)
                    msg.append(c)
                    msg.append(bytes(ec.error))
                    log.error(f'Error saving pipeline: {ec.error}')
                except SerializeIDError as ex:
                    c = bytes(ManageStatus.PipelineSerializationError)
                    msg.append(c)
                    msg.append(str(ex).encode())
                    log.error(f'Error saving pipeline: {ex}')
            case ManageRequest.DeletePipeline:
                try:
                    pipeline_list = self._delete_pipeline(data)
                    msg.append(bytes(ManageStatus.Ok))
                    msg.extend(pipeline_list)
                except MessageError as ec:
                    c = bytes(ManageStatus.PipelineMessageError)
                    msg.append(c)
                    msg.append(bytes(ec.error))
                    log.error(f'Error deleting pipeline: {ec.error}')
            case ManageRequest.ListPipelines:
                msg.append(bytes(ManageStatus.Ok))
                msg.extend(self._list_pipelines())
            case ManageRequest.Unknown:
                msg.append(bytes(ManageStatus.UnknownRequest))

        self.management.send_multipart(msg)

    def run(self):
        running = True
        while running:
            try:
                socks = dict(self.poller.poll())
            except KeyboardInterrupt:
                # We use the shutdown signal here instead of just
                # breaking, so that all shutdown code is handled in
                # the same place if we decide to do additional cleanup
                self.shutdown_signal.send(b'')
                continue

            if self.shutdown_sink in socks:
                running = False

            if self.management in socks:
                self._manage()

            if self.router not in socks:
                continue

            msg_parts = self.router.recv_multipart()
            client_id = msg_parts[0]
            data = msg_parts[2:]

            match data[0]:
                case b'\x00':
                    log.info('Decompiler registered, loading plugins')
                    msg_parts = [client_id, b'']

                    # TODO: Do some sanity checking to make sure we are
                    # not sending garbage to the decompiler process (or
                    # let the decompiler handle it)
                    plugin_paths = [
                        str(p.file_path).encode()
                        for p in self.plugins
                    ]

                    # Make sure we at least send an empty message if we
                    # don't have any plugins to load
                    if plugin_paths:
                        msg_parts.extend(plugin_paths)
                    else:
                        msg_parts.append(b'')

                    self.router.send_multipart(msg_parts)
                case b'\x01':
                    msg_parts = [client_id, b'']
                    try:
                        current_p = self.current_pipeline
                        p = self._list_pipeline_for_decomp(current_p)
                        msg_parts.append(struct.pack('<Q', self.pipeline_id))
                        msg_parts.extend(p)
                    except SerializeIDError:
                        msg_parts.extend([b'NOK'])

                    self.router.send_multipart(msg_parts)
                case b'\x02':
                    log.info(f'recv: {data[1].decode()}')
                    self.router.send_multipart([client_id, b'', b'OK'])
                case b'\x03':
                    log.info('decompiler checking for pipeline update')
                    pid = struct.pack('<Q', self.pipeline_id)
                    self.router.send_multipart([client_id, b'', pid])
                case _:
                    log.info(f'recv: {data[0].decode()}')
                    self.router.send_multipart([client_id, b'', b'OK'])


@contextmanager
def start_background(config_path: Path):
    r = ReOxideManager(config_path, log_to_buffer=True)
    t = threading.Thread(target=r.run)

    try:
        t.start()
        yield r
    finally:
        r.shutdown()
        t.join()


def main_cli():
    parser = argparse.ArgumentParser()
    parser.description = 'ReOxide daemon for communication with decompiler instances'
    parser.add_argument(
        '--no-adjust-loader-path',
        required=False,
        action='store_true',
        help='If specified, do not start new process with '\
            'adjusted LD_LIBRARY_PATH. The daemon has to '\
            'adjust the path for loading native plugin '\
            'libraries and will restart itself with the'\
            'adjust path if this flag is not passed.'
    )
    parser.add_argument(
        '-c',
        '--config',
        required=False,
        type=Path,
        help='Specifies path for the reoxide.toml config file'
    )

    # Note, for the bind arguments, we do NOT want to use the default
    # arguments from argparse, because we want to have the command line
    # arg take precedence over environment variables when provided
    parser.add_argument(
        '-b',
        '--bind',
        required=False,
        type=str,
        help='ZMQ listener socket for decompiler connections, ' \
            'can also be set with env var REOXIDE_BIND. ' \
            'default: ipc:///tmp/reoxide.sock'
    )
    parser.add_argument(
        '-m',
        '--manage-bind',
        required=False,
        type=str,
        help='ZMQ listener socket for configuring ReOxide, ' \
            'can also be set with env var REOXIDE_MANAGE_BIND. ' \
            'default: ipc:///tmp/reoxide-manage.sock'
    )

    args = parser.parse_args()

    format = '%(asctime)s %(levelname)s %(name)s - %(message)s'
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format=format,
        datefmt="%Y-%m-%dT%H:%M:%S"
    )

    # For the plugins to work, we need to add the binary folder to the
    # LD_LIBRARY_PATH. Setting the env var from a running process does
    # not change the dlopen behavior, so we need to start a new process
    # for that.
    if not args.no_adjust_loader_path:
        bin_path = ld_library_path()
        env = dict(os.environ)
        env['LD_LIBRARY_PATH'] = str(bin_path)
        args = sys.orig_argv + ['--no-adjust-loader-path']
        path = sys.executable
        log.info('Restarting with updated LD_LIBRARY_PATH...')
        os.execve(path, args, env)

    # We either take the config file from the args, use the env var
    # or use the platform dir per default
    config_path = args.config
    if config_path:
        config_path = config_path_check(config_path)
    else:
        if REOXIDE_CONFIG:
            config_path = config_path_check(Path(REOXIDE_CONFIG))
        else:
            from platformdirs import user_config_path
            config_dir = user_config_path(APP_NAME, APP_AUTHOR)
            config_path = config_dir / 'reoxide.toml'
            config_path = config_path_check(config_path)

    try:
        manager = ReOxideManager(
            config_path,
            bind=args.bind,
            manage_bind=args.manage_bind
        )
        manager.run()
    except ReOxideError as e:
        log.error(e)
