#!/usr/bin/env python3

"""
dotsync syncs dotfiles to remote hosts.

Prerequisites:
- A modern rsync version (with --mkpath support)

Beneficial:
- Cache SSH connections for even faster syncs, with something like the following in your ~/.ssh/config:

Host *
  ControlMaster auto
  ControlPath ~/.ssh/sockets/%r@%h-%p
  ControlPersist 600
"""

import asyncio
import hashlib
import os
import platform
import re
import shutil
import socket
import subprocess
import tempfile
import time
import traceback
import typing as t
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path as StdPath
from random import randint

import click
import yaml
from anyio import Path
from click_aliases import ClickAliasedGroup
from click_default_group import DefaultGroup
from coda import getenv_bool
from jinja2 import Environment, StrictUndefined
from pydantic import AfterValidator, BaseModel, ConfigDict
from watchfiles import awatch

DEBUG = False or getenv_bool("DOTSYNC_DEBUG")

# To sync efficiently, we use a 3-layer approach:
#   1. Source layer: actual listed source files to be synced
#   2. Watch layer: [watch cmd] hard links to source files for filesystem watching (optimistically reduces required watches)
#   3. Staging layer: [sync manager] metadata-preserving copies (or materialized templates) to be batch-rsynced to remote hosts (reduces rsync calls when large # src files/changes)

# Example config:
#
# groups:
#   work:
#     user: admin
#     vars: { company: pinterest }
#     paths:
#       /local/src: /remote/dst
#
# hosts:
#   devapp:
#     tags: [ personal, work ]      # tags organize hosts and inject group paths
#     user: admin                   # override user for ssh/rsync
#     vars: { env: production }     # vars when templating *.tpl.j2 files
#     paths:
#       /local/src: /remote/dst     # src can be a .tpl.j2 file and will be rendered with vars


P = t.TypeVar("P", str, Path)


def paths_validator(v: dict[P, str]) -> dict[P, str]:
    """
    Validate the following:
    - Src paths
        - Not empty
    - Dst paths
        - Not empty
        - Non-relative (either leading / or leading ~/)
    """
    for src, dst in v.items():
        if not src:
            raise ValueError("source path cannot be empty")
        if not dst:
            raise ValueError("destination path cannot be empty")
        if not (dst.startswith("/") or dst.startswith("~/")):
            raise ValueError(f"destination path '{dst}' must be absolute (start with '/') or home-relative (start with '~/')")
    return v


class GroupConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    user: str | None = None
    vars: dict[str, t.Any] | None = dict()
    paths: dict[str, str] | None = dict()  # src -> dst


GroupConfigs = dict[str, GroupConfig]  # name -> config


class HostConfigBase(BaseModel):
    tags: list[str] = []
    user: str | None = None
    vars: dict[str, t.Any] = dict()


class HostConfig(HostConfigBase):
    model_config = ConfigDict(frozen=True)

    paths: t.Annotated[dict[str, str], AfterValidator(paths_validator)] = dict()  # src -> dst


class MatHostConfig(HostConfigBase):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    paths: t.Annotated[dict[Path, str], AfterValidator(paths_validator)] = dict()  # src -> dst


HostConfigs = dict[str, HostConfig]  # hostname -> config

MatHostConfigs = dict[str, MatHostConfig]  # hostname -> config

HostPath = t.Tuple[str, str]  # (host, dst)

LocalToRemotes = dict[Path, list[HostPath]]  # src -> list of (host, dst)


class Config(BaseModel):
    model_config = ConfigDict(frozen=True)

    groups: GroupConfigs = dict()
    hosts: HostConfigs = dict()

    async def materialize(self) -> "MatConfig":
        """
        Materialize config by resolving paths to Path objects.

        Host-level overrides group-level.
        """
        hosts: MatHostConfigs = dict()
        for host, host_config in self.hosts.items():
            mat_user: str | None = None
            mat_vars: dict[str, t.Any] = dict()
            mat_paths: dict[Path, str] = dict()

            layers: list[GroupConfig | HostConfig] = [g for tag in host_config.tags if (g := self.groups.get(tag))] + [host_config]
            for layer in layers:
                mat_user = layer.user if layer.user is not None else mat_user
                mat_vars.update(layer.vars or {})
                mat_paths.update({await resolve(src): dst for src, dst in (layer.paths or {}).items()})

            hosts[host] = MatHostConfig(user=mat_user, vars=mat_vars, paths=mat_paths)

        return MatConfig(hosts=hosts)


class MatConfig(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    hosts: MatHostConfigs = dict()

    def select(self, remotes: list[str] | tuple[str, ...] | None = None) -> "MatConfig":
        """Return config filtered by remotes."""
        if not remotes:
            return self
        for remote in remotes:
            if not self._has(remote):
                debug(f"remote '{remote}' not found in config; skipping")
        return MatConfig(hosts={k: v for k, v in self.hosts.items() if any(self._matches(k, v, remote) for remote in remotes)})

    def resolve_host(self, hostname: str, *, inject_hostname: bool = False) -> "MatConfig | None":
        """Select the best matching host for a given hostname."""
        if hostname.startswith("@"):
            raise click.ClickException("select_best requires a specific hostname, not a @tag")

        if hostname in self.hosts:
            return MatConfig(hosts={hostname: self.hosts[hostname]})

        matches: list[str] = []
        for host, cfg in self.hosts.items():
            simple_pat = re.escape(host).replace(r"\*", ".*")
            try:
                debug(f"checking if host '{hostname}' matches pattern '{host}'")
                if re.fullmatch(simple_pat, hostname):
                    matches.append(host)
            except re.error:
                warn(f"invalid pattern '{host}' in config; skipping")
        if not matches:
            debug(f"host '{hostname}' did not match any patterns")
            return None

        sorted_matches = sorted(matches, key=lambda x: len(x), reverse=True)
        debug(f"host '{hostname}' matched patterns: {sorted_matches}")

        host = hostname if inject_hostname else sorted_matches[0]
        host_cfg = self.hosts[sorted_matches[0]]
        return MatConfig(hosts={host: host_cfg})

    async def local_to_remotes(self) -> LocalToRemotes:
        """Get a mapping of local src paths to remote (host, dst) pairs."""
        ltr: LocalToRemotes = dict()
        for host in self.hosts:
            for src_path, dst in (await self.host_paths(host)).items():
                ltr[src_path] = ltr.get(src_path, [])
                ltr[src_path].append((host, dst))
        return ltr

    async def host_paths(self, host: str, include_missing: bool = False) -> dict[Path, str]:
        """Get a mapping of local src paths to remote dst for a given host."""
        if host not in self.hosts:
            raise click.ClickException(f"host '{host}' not found in config")

        paths = self.hosts[host].paths
        existing = {src: dst for src, dst in paths.items() if await src.exists()}
        missing = {Path(f"[MISSING] {src}"): dst for src, dst in paths.items() if not await src.exists()}

        ltr = deepcopy(existing)
        if include_missing:
            ltr.update(missing)
        else:
            for missing_path in missing.keys():
                warn(f"[{host}] {missing_path} source path does not exist; skipping")

        debug(f"host '{host}' paths ({len(ltr)}): {ltr}")
        return ltr

    def host_vars(self, host: str) -> dict[str, t.Any]:
        """Get a mapping of vars for a given host."""
        if host not in self.hosts:
            raise click.ClickException(f"host '{host}' not found in config")
        v = deepcopy(self.hosts[host].vars)
        return v

    def _has(self, remote: str) -> bool:
        """
        Check if a remote is in the config.

        A remote is either a @tag or a hostname.
        """
        if remote.startswith("@"):
            tag = remote[1:]
            return any(tag in host_config.tags for host_config in self.hosts.values())
        return remote in self.hosts

    @staticmethod
    def _matches(host_name: str, host_config: MatHostConfig, remote: str) -> bool:
        """
        Check if a host_config matches a remote.

        A remote is either a @tag or a hostname.
        """
        if remote.startswith("@"):
            tag = remote[1:]
            return tag.lower() in (tt.lower() for tt in host_config.tags)
        return host_name.lower() == remote.lower()


def std_config_dir() -> StdPath:
    """Get the dotsync configuration directory. Sync to work well with click."""
    return StdPath(os.environ.get("DOTSYNC_CONFIG_DIR", "~/.config/dotsync")).expanduser()


async def config_dir() -> Path:
    """Get the dotsync configuration directory."""
    return await Path(os.environ.get("DOTSYNC_CONFIG_DIR", "~/.config/dotsync")).expanduser()


def config_path(_: click.Context, __: click.Parameter, cpath: Path | None) -> Path:
    """Get the dotsync configuration file path for initialization."""
    return asyncio.run(_config_path(cpath))


async def _config_path(cpath: Path | None) -> Path:
    if cpath is not None:
        resolved = await resolve(cpath)
        if not await resolved.exists():
            raise click.ClickException(f"No configuration file found at {resolved}. Please run 'dotsync init' to create one.")
        return resolved

    base_dir = await config_dir()
    paths = [base_dir / f for f in [f"{hostname_short()}.dotsync.yaml", "dotsync.yaml"]]
    for p in paths:
        resolved = await resolve(p)
        if await resolved.exists():
            return resolved

    # Couldn't find a default-location config file
    raise click.ClickException(f"No configuration file found in {base_dir}. Please run 'dotsync init' to create one.")


async def conf(cpath: Path) -> MatConfig:
    """Load dotsync configuration from the given path."""
    try:
        config = Config.model_validate(yaml.safe_load(await cpath.read_text()) or {})
    except (ValueError, yaml.YAMLError) as e:
        raise click.ClickException(f"Failed parsing config file {cpath}: {e}")

    return await config.materialize()


async def conf_select(cpath: Path, remotes: list[str] | tuple[str, ...] | None = None) -> MatConfig:
    """Load and select dotsync configuration from the given path."""
    return (await conf(cpath)).select(remotes)


def hn_platform() -> str:
    return platform.node().split(".")[0]


def hn_socket() -> str:
    return socket.gethostname().split(".")[0]


def hn_env() -> str:
    return os.environ.get("HOSTNAME", "").split(".")[0]


def hostname_short() -> str:
    """Get the short hostname of the current machine."""
    for func in (hn_platform, hn_socket, hn_env):
        try:
            hn = func()
            if hn:
                return hn
        except (IndexError, AttributeError, OSError):
            continue
    raise click.ClickException("Failed to determine hostname from platform, socket, or environment.")


class AliasedDefaultGroup(ClickAliasedGroup, DefaultGroup):
    pass


@click.group(
    cls=AliasedDefaultGroup,
    default="sync",
    default_if_no_args=True,
    context_settings=dict(
        help_option_names=["-h", "--help"],
        max_content_width=120,
    ),
)
def cli():
    """CLI for syncing dotfiles to remote hosts."""
    pass


@dataclass
class ConcurConfig:
    src_concur: int
    coalesce_secs: float = 0  # set via --coalesce-secs


config_option = click.option(
    "--config",
    "-c",
    "cpath",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, path_type=Path),
    callback=config_path,
    help="Path to the dotsync configuration file. Defaults to searching in $DOTSYNC_CONFIG_DIR or ~/.dotsync for <hostname>.dotsync.yaml then dotsync.yaml",
)
src_concur_option = click.option("--src-concur", "src_concur", type=int, default=30, show_default=True, help="Maximum concurrent source file syncs.")
force_option = click.option("--force", is_flag=True, default=False, help="Force overwrite of existing files on remote hosts.")
dry_run_option = click.option(
    "--dry",
    "--dry-run",
    "dry_run",
    is_flag=True,
    default=False,
    help="Only show what would be synced, without performing any actions.",
)
verbose_option = click.option("--verbose", "-v", is_flag=True, default=getenv_bool("DOTSYNC_VERBOSE"), help="Enable verbose output.")


@cli.command(name="sync", aliases=["s"])
@config_option
@src_concur_option
@force_option
@dry_run_option
@verbose_option
@click.argument("remotes", nargs=-1)
def sync_cmd(cpath: Path, src_concur: int, force: bool, dry_run: bool, verbose: bool, remotes: tuple[str, ...]):
    """
    Sync dotfiles to remote machines based on configuration.

    REMOTES: optional list of remotes (either hostnames or @tags) to sync to; if not provided, syncs to all configured hosts.
    """
    with tempfile.TemporaryDirectory(prefix=f"dotsync-sync-{tmp_prefix_uniq()}-") as tmpdir:
        asyncio.run(_sync_cmd(cpath, ConcurConfig(src_concur), force, dry_run, verbose or DEBUG, remotes, tmpdir=tmpdir))


async def _sync_cmd(
    cpath: Path,
    concur: ConcurConfig,
    force: bool,
    dry_run: bool,
    verbose: bool,
    remotes: tuple[str, ...],
    *,
    tmpdir: str,
    override_config: MatConfig | None = None,
):
    tmpdir_resolved = await Path(tmpdir).resolve()
    staging_dir = tmpdir_resolved / "staging"

    if override_config:
        debug("using override config for sync command")

    config = override_config or await conf_select(cpath, remotes)

    manager = SyncManager(concur, staging_dir)
    manager.start(config)

    try:
        for host in config.hosts:
            for src_path, dst in (await config.host_paths(host)).items():
                await manager.put(Job(host, config.host_vars(host), src_path, dst, force, dry_run, verbose))
        await manager.drain()
    finally:
        await manager.stop()


@cli.command(name="watch", aliases=["w"])
@config_option
@src_concur_option
@click.option("--coalesce-secs", "coalesce_secs", type=float, default=3.0, show_default=True, help="Seconds to coalesce rapid changes to the same file.")
@force_option
@dry_run_option
@verbose_option
@click.argument("remotes", nargs=-1)
def watch_cmd(cpath: Path, src_concur: int, coalesce_secs: float, force: bool, dry_run: bool, verbose: bool, remotes: tuple[str, ...]):
    """
    Watch dotfiles for changes and sync automatically.

    REMOTES: optional list of remotes (either hostnames or @tags) to watch for; if not provided, watches for all configured hosts.
    """
    if coalesce_secs < 0:
        raise click.ClickException("--coalesce-secs must be non-negative")

    with tempfile.TemporaryDirectory(prefix=f"dotsync-watch-{tmp_prefix_uniq()}-") as tmpdir:
        asyncio.run(_watch_cmd(cpath, ConcurConfig(src_concur, coalesce_secs), force, dry_run, verbose or DEBUG, remotes, tmpdir=tmpdir))


async def _watch_cmd(cpath: Path, concur: ConcurConfig, dry_run: bool, force: bool, verbose: bool, remotes: tuple[str, ...], *, tmpdir: str):
    tmpdir_resolved = await Path(tmpdir).resolve()
    staging_dir = tmpdir_resolved / "staging"
    watch_dir = tmpdir_resolved / "watch"

    manager = SyncManager(concur, staging_dir)

    async def reconfig() -> MatConfig:
        cfg = await conf_select(cpath, remotes)
        await manager.reconfigure(cfg, timeout=5.0)
        return cfg

    async def watch_changes(cfg: MatConfig) -> int:
        ltr = await cfg.local_to_remotes()
        watch_area = await setup_watch_area(Path(watch_dir), list(ltr.keys()))
        click.echo(f"Watching {len(ltr)} source paths... (press ctrl+c to stop)")
        async for change_set in awatch(watch_area.dir, *watch_area.missing, cpath):
            for change, change_path in change_set:
                cp = await Path(change_path).resolve()
                src_path = watch_area.watch_to_src.get(cp, cp)
                if verbose or DEBUG:
                    click.echo(f"[{change.name}] {src_path}")
                if src_path == cpath:
                    click.echo("\n[RELOAD] config file changed\n")
                    return 1  # avoid hot-looping
                if src_path not in ltr:
                    debug(f"change detected for unconfigured file {src_path}; skipping")
                    continue
                for host, dst in ltr[src_path]:
                    await manager.put(Job(host, cfg.host_vars(host), src_path, dst, force, dry_run, verbose))

    config = await reconfig()
    try:
        while True:
            if delay := await watch_changes(config):
                await asyncio.sleep(delay)
            config = await reconfig()
    except (KeyboardInterrupt, asyncio.CancelledError):
        click.echo("Stopping watch")
    finally:
        await manager.stop()


@cli.command(name="ssh", aliases=["h"])
@config_option
@src_concur_option
@force_option
@verbose_option
@click.argument("hostname", type=str)
def ssh_cmd(cpath: Path, src_concur: int, force: bool, verbose: bool, hostname: str):
    """
    SSH into a remote host configured in dotsync.

    HOST: remote hostname to SSH into.
    """
    asyncio.run(_ssh_cmd(cpath, src_concur, force, verbose, hostname))


async def _ssh_cmd(cpath: Path, src_concur: int, force: bool, verbose: bool, hostname: str):
    if hostname.startswith("@"):
        raise click.ClickException("ssh command requires a specific hostname, not a @tag")

    config = await conf(cpath)
    override_config: MatConfig

    hosts = config.select([hostname]).hosts
    if len(hosts) == 1:
        override_config = MatConfig(hosts=hosts)
    elif len(hosts) > 1:  # shouldn't happen
        raise click.ClickException(f"multiple remotes matched for '{hostname}'")
    else:  # no hosts found
        debug(f"no direct match for host '{hostname}'; trying pattern match")
        override_config = config.resolve_host(hostname, inject_hostname=True)

    if not override_config or not override_config.hosts:
        raise click.ClickException(f"host '{hostname}' not found in config")

    with tempfile.TemporaryDirectory(prefix=f"dotsync-ssh-{tmp_prefix_uniq()}-") as tmpdir:
        await _sync_cmd(cpath, ConcurConfig(src_concur), force, False, verbose or DEBUG, (hostname,), override_config=override_config, tmpdir=tmpdir)

    os.execvp("ssh", ["ssh", hostname])


@cli.command(name="edit", aliases=["e"])
@config_option
@click.option("--editor", "-e", "editor", type=str, default=os.environ.get("EDITOR", "vi"), show_default=True, help="Editor to use for editing the config file")
def edit_cmd(cpath: Path, editor: str | None):
    """Edit dotfiles configuration file."""
    if not shutil.which(editor):
        raise click.ClickException(f"Editor '{editor}' not found; please pass or set the $EDITOR environment variable to a valid editor.")
    os.execvp(editor, [editor, str(cpath)])


@cli.command(name="show", aliases=["o"])
@config_option
@click.argument("remotes", nargs=-1)
def show_cmd(cpath: Path, remotes: tuple[str, ...]):
    """
    Show dotfiles to be synced based on configuration.

    REMOTES: optional list of remotes (either hostnames or @tags) to show; if not provided, shows all configured hosts.
    """
    asyncio.run(_show_cmd(cpath, remotes))


async def _show_cmd(cpath: Path, remotes: tuple[str, ...]):
    click.echo(f"From {cpath} for {hostname_short()}")

    msg = "matching" if remotes else "configured"
    is_single_host = len(remotes) == 1 and not remotes[0].startswith("@")

    config = await conf(cpath)
    config_for_remotes = config.select(remotes)
    if not config_for_remotes.hosts and is_single_host:
        override_config = config.resolve_host(remotes[0])
        if override_config and override_config.hosts:
            host = list(override_config.hosts.keys())[0]
            click.echo(f"<no matching remotes, but for ssh '{remotes[0]}' would match host '{host}'>")
            config_for_remotes = override_config

    if not config_for_remotes.hosts:
        click.echo(f"\n<no {msg} remotes>")

    for host, host_config in config_for_remotes.hosts.items():
        tags = host_config.tags or []
        v = config_for_remotes.host_vars(host)
        paths = await config_for_remotes.host_paths(host, include_missing=True)

        click.echo(f"\n{host}:")

        click.echo("  tags:")
        for tag in tags:
            click.echo(f"    - {tag}")

        click.echo("  vars:")
        for k, v in v.items():
            click.echo(f"    {k}: {v}")

        click.echo("  paths:")
        for src_path, dst in paths.items():
            click.echo(f"    {src_path} -> {host}:{dst}")


@cli.command(name="init", aliases=["i"])
@click.option(
    "--config",
    "-c",
    "cpath",
    type=click.Path(file_okay=True, dir_okay=False, path_type=StdPath),
    help="Path to the dotsync configuration file. Overrides --dir and --file if specified.",
)
@click.option(
    "--dir",
    "-d",
    "cdir",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, path_type=StdPath),
    default=std_config_dir(),
    help="Directory to initialize dotsync configuration file in. Defaults to ~/.dotsync, or $DOTSYNC_CONFIG_DIR if set.",
)
@click.option(
    "--file",
    "-f",
    "filename",
    default="dotsync.yaml",
    help="Name of the configuration file to create. Defaults to <hostname>.dotsync.yaml",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing configuration file if it exists.",
)
@click.argument("hosts", nargs=-1)
def init_cmd(cpath: StdPath | None, cdir: StdPath, filename: str, force: bool, hosts: tuple[str, ...]):
    """
    Initialize dotfiles configuration on the current machine.

    HOSTS: optional list of remote hostnames to include in the config; if not provided, includes example hosts.
    """
    asyncio.run(_init_cmd(Path(cpath) if cpath else None, Path(cdir) if cdir else None, filename, force, hosts))


async def _init_cmd(cpath: Path | None, cdir: Path, filename: str, force: bool, hosts: tuple[str, ...]):
    path = cpath or await resolve(cdir) / filename
    if await path.exists() and not force:
        raise click.ClickException(f"Configuration file already exists at {path}. Use --force to overwrite.")

    await path.parent.mkdir(parents=True, exist_ok=True)
    await path.write_text(await lorem(hosts))

    click.echo(f"Initialized {path} with example contents")


async def lorem(hosts: tuple[str, ...]) -> str:
    """Create a lorem ipsum config based on presence of well-known dotfiles."""
    lines = [
        f"# Dotsync: example config for {hostname_short()}",
        "#",
        "# Structure:",
        "#",
        "# hosts:",
        "#    remote-hostname:",
        "#      tags: [ optional, tags ]                # tags organize hosts and inject group paths",
        "#      user: admin                             # override user for ssh/rsync",
        "#      vars: { key: value }                    # vars when templating *.tpl.j2 files",
        "#      paths:",
        "#        /local/src/path: /remote/dst/path     # src can be a .tpl.j2 file and will be rendered with vars",
        "",
    ]

    hosts = hosts or ("host1", "host2")
    files = [
        f
        for f in (
            await path_if_exists("~/.bash_aliases"),
            await path_if_exists("~/.bash_profile"),
            await path_if_exists("~/.bashrc"),
            await path_if_exists("~/.gitconfig"),
            await path_if_exists("~/.vimrc"),
            await path_if_exists("~/.zshenv"),
            await path_if_exists("~/.zshrc"),
        )
        if f is not None
    ] or ["~/.bashrc", "~/.vimrc"]
    config = Config(hosts={host: HostConfig(paths={f: f for f in files}) for host in hosts})
    lines.append(yaml.safe_dump(config.model_dump(exclude_unset=True), sort_keys=True))

    return "\n".join(lines)


class TemplateEngine:
    """Template engine for rendering dotfiles with host-specific variables."""

    def __init__(self, ctx: dict[str, t.Any]):
        self.env = Environment(enable_async=True, undefined=StrictUndefined, keep_trailing_newline=True)
        self.ctx = ctx

    async def render(self, src_path: Path, dst_path: Path):
        """Render a template file with the given variables into a temporary file, returning the rendered path."""
        if not is_tpl(src_path):
            raise ValueError(f"Source path {src_path} is not a .tpl.j2 template file")

        await dst_path.parent.mkdir(parents=True, exist_ok=True)

        template = self.env.from_string(await src_path.read_text())
        rendered = await template.render_async(**self.ctx)

        await dst_path.write_text(rendered)


@dataclass
class Job:
    """A single sync job for a source file to a remote host."""

    host: str
    vars: dict[str, t.Any]
    src_path: Path
    dst: str

    force: bool
    dry_run: bool
    verbose: bool

    def dst_relative_to(self, home: Path, root: Path) -> t.Tuple[Path | None, Path | None]:
        """Get the destination path relative to home or root, returning (home-relative, root-relative)."""
        if self.dst.startswith("~/"):
            return home / without_tpl(self.dst[2:]), None
        if self.dst.startswith("/"):
            return None, root / without_tpl(self.dst[1:])
        raise ValueError(f"destination path '{self.dst}' is not absolute or home-relative")


@dataclass
class Batch:
    """A batch of sync jobs for a single host."""

    jobs: list[Job]
    stag: "StagingArea"

    done_evt: asyncio.Event = field(default_factory=asyncio.Event)
    retries: int = 0

    def __str__(self) -> str:
        if not self.jobs:
            return f"[{self.host}] <no jobs>"
        return f"[{self.host}] {', '.join(f'{j.src_path} -> {j.dst}' for j in self.jobs)}"

    def has_home_relative_dsts(self) -> bool:
        """Check if any job in the batch has a home-relative destination."""
        return any(j.dst.startswith("~/") for j in self.jobs)

    def has_root_relative_dsts(self) -> bool:
        """Check if any job in the batch has a root-relative destination."""
        return any(j.dst.startswith("/") for j in self.jobs)

    @property
    def host(self) -> str:
        if not self.jobs:
            raise ValueError("Batch has no jobs")
        return self.jobs[0].host

    @property
    def vars(self) -> dict[str, t.Any]:
        if not self.jobs:
            raise ValueError("Batch has no jobs")
        return self.jobs[0].vars

    @property
    def force(self) -> bool:
        if not self.jobs:
            raise ValueError("Batch has no jobs")
        return self.jobs[0].force

    @property
    def dry_run(self) -> bool:
        if not self.jobs:
            raise ValueError("Batch has no jobs")
        return self.jobs[0].dry_run

    @property
    def verbose(self) -> bool:
        if not self.jobs:
            raise ValueError("Batch has no jobs")
        return self.jobs[0].verbose


class HostPipeline:
    """A pipeline of sync jobs for a single host."""

    def __init__(self, host: str, tpl: TemplateEngine, sem: asyncio.Semaphore):
        self.host = host
        self.tpl = tpl

        self.sem = sem

        self.q = asyncio.Queue[Batch]()
        self.worker: asyncio.Task | None = None
        self.draining: bool = False

    def start(self):
        """Start worker tasks for the pipeline."""
        self.worker = asyncio.create_task(self._worker())

    async def drain(self):
        """Drain all jobs from the pipeline."""
        self.draining = True
        debug(f"[{self.host}] draining pipeline: {self.q.qsize()} queued")
        await self.q.join()

    async def stop(self):
        """Stop all worker tasks for the pipeline."""
        self.worker.cancel()
        await asyncio.gather(self.worker, return_exceptions=True)

    async def put(self, batch: Batch):
        """Enqueue an action to the pipeline."""
        if batch.host != self.host:
            raise ValueError(f"Action host '{batch.host}' does not match pipeline host '{self.host}'")
        if self.draining:
            debug(f"[{self.host}] ignoring batch job during drain")
            return
        await self.q.put(batch)

    async def _worker(self):
        """Worker task to process sync jobs from the queue."""
        while True:
            batch = await self.q.get()
            async with self.sem:
                try:
                    await self._sync(batch)
                    batch.done_evt.set()  # success
                except Exception as e:
                    err(f"[{self.host}] failed to sync batch: {e}")
                    batch.retries += 1
                    if batch.retries > 3:
                        err(f"[{self.host}] exceeded maximum retries for batch; dropping")
                        batch.done_evt.set()  # failure
                    else:
                        warn(f"[{self.host}] retrying batch (attempt {batch.retries}/3)")
                        await self.q.put(batch)  # requeue
                finally:
                    self.q.task_done()

    @staticmethod
    async def _sync(batch: Batch):
        """Perform the sync for a given batch."""
        debug(f"[{batch.host}] syncing {len(batch.jobs)} jobs: {batch}")
        await rsync(batch, dryrun=batch.dry_run)


class SyncManager:
    """Manages sync jobs across multiple hosts, including lifecycle management."""

    def __init__(self, concur: ConcurConfig, tmp_dir: Path):
        self.q = asyncio.Queue[Job]()
        self.worker: asyncio.Task | None = None
        self.draining: bool = False
        self.in_flight: set[asyncio.Task] = set()
        self.pipelines: dict[str, HostPipeline] = dict()

        self.sem = asyncio.Semaphore(concur.src_concur)
        self.coalesce_secs = concur.coalesce_secs

        self.tmp_dir = tmp_dir
        self.staging_dir: Path | None = None

        self.last_sync: float = 0  # time.monotonic()

    def start(self, config: MatConfig):
        """Configure pipelines based on the given config."""
        debug(f"config SyncManager with {len(config.hosts)} hosts")
        self.draining = False
        if self.pipelines:
            raise click.ClickException("SyncManager is already configured; use reconfigure() to change configuration")
        self.staging_dir = self.tmp_dir / f"staging-{tmp_prefix_uniq()}"
        for host in config.hosts:
            self.pipelines[host] = HostPipeline(
                host,
                TemplateEngine(config.host_vars(host)),
                self.sem,
            )
            self.pipelines[host].start()
        self.worker = asyncio.create_task(self._worker())

    async def drain(self):
        """Drain all pipelines."""
        self.draining = True
        debug(f"SyncManager draining: {self.q.qsize()} queued jobs")
        await self.q.join()

        if self.in_flight:
            debug(f"SyncManager waiting for {len(self.in_flight)} in-flight batch cleanups")
            await asyncio.gather(*self.in_flight)

        if self.pipelines:
            debug(f"SyncManager draining {len(self.pipelines)} pipelines")
            await asyncio.gather(*(p.drain() for p in self.pipelines.values()))

    async def stop(self):
        """Stop all pipelines."""
        debug(f"SyncManager stopping {len(self.pipelines)} pipelines")
        self.worker.cancel()
        await asyncio.gather(self.worker, return_exceptions=True)
        if self.pipelines:
            await asyncio.gather(*(p.stop() for p in self.pipelines.values()))

    async def put(self, job: Job):
        """Enqueue a sync batch to the appropriate host pipeline."""
        if job.host not in self.pipelines:
            raise click.ClickException(f"No pipeline for host '{job.host}'; ensure reconfigure() has been called")
        if self.draining:
            debug("ignoring batch job during drain")
            return
        await self.q.put(job)

    async def reconfigure(self, config: MatConfig, *, timeout: float):
        """Reconfigure pipelines based on the given config."""
        debug(f"reconfig SyncManager from {len(self.pipelines)} to {len(config.hosts)} hosts")
        if self.pipelines:
            debug(f"reconfig: draining {len(self.pipelines)} existing pipelines")
            try:
                await asyncio.wait_for(self.drain(), timeout=timeout)
            except asyncio.TimeoutError:
                warn("drain timeout reached; forcing pipeline rotations to proceed with reconfig")
            await self.stop()
            self.pipelines.clear()

        if self.staging_dir and await self.staging_dir.exists():
            await asyncio.to_thread(shutil.rmtree, str(self.staging_dir), ignore_errors=False, onerror=None)

        self.start(config)

    async def _delay(self, batch_id: int):
        """How long to wait for coalescing more jobs."""
        since_last = time.monotonic() - self.last_sync
        if since_last < self.coalesce_secs:
            wait = self.coalesce_secs - since_last
            debug(f"batch wait: {wait:.2f}s (since last sync {since_last:.2f}s ago with coalesce_secs={self.coalesce_secs:.2f}s)")
            await asyncio.sleep(wait)
            return

        debug(f"[batch {batch_id}] no recent syncs; proceeding immediately")
        await asyncio.sleep(0.2)  # short wait to slurp more changes

    async def _worker(self):
        """Batch changes from the main queue, prepare a staging area for the batch, and dispatch to host pipelines."""
        batch_id = -1
        failures = 0
        while True:
            batch_id += 1
            try:
                await self._sync_batch(batch_id)
            except Exception as e:
                err(f"failed to sync batch {batch_id}: {e}")
                if DEBUG:
                    traceback.print_exc()
                failures += 1
                if failures >= 5:
                    err("too many consecutive batch failures; stopping SyncManager worker")
                    raise
                await asyncio.sleep(5)  # avoid hot-looping

    async def _sync_batch(self, batch_id: int):
        """Perform the sync for a given batch."""
        # Signal: need to process a batch
        jobs: list[Job] = [await self.q.get()]

        # Slurp: wait a short time for more jobs to batch together
        await self._delay(batch_id)  # either short wait for slurp or longer wait for coalesce
        while not self.q.empty():
            jobs.append(self.q.get_nowait())

        # Stage: prepare staging area for batch
        batch_staging_dir = self.staging_dir / f"batch-{batch_id}"
        debug(f"[batch {batch_id}] preparing staging area at {batch_staging_dir} with {len(jobs)} jobs")
        await batch_staging_dir.mkdir(parents=True, exist_ok=True)
        stag = await StagingArea(batch_staging_dir).stage(jobs)

        # Group: group into host-wise batches
        host_to_jobs: t.DefaultDict[str, list[Job]] = defaultdict(list)
        for j in jobs:
            host_to_jobs[j.host].append(j)
        host_to_batches: dict[str, Batch] = {h: Batch(jj, stag) for h, jj in host_to_jobs.items()}

        # Dispatch: send jobs to host pipelines
        for host, batch in host_to_batches.items():
            await self.pipelines[host].put(batch)

        # Cleanup: remove staging area for batch
        gc = asyncio.create_task(self._gc_batch(batch_id, batch_staging_dir, [b.done_evt for b in host_to_batches.values()]))
        self.in_flight.add(gc)
        gc.add_done_callback(self.in_flight.discard)

        # Complete: mark batch jobs as processed
        for _ in jobs:
            self.q.task_done()
        self.last_sync = time.monotonic()

    @staticmethod
    async def _gc_batch(batch_id: int, path: Path, done_evts: list[asyncio.Event]):
        try:
            await asyncio.gather(*(evt.wait() for evt in done_evts))
            if await path.exists():
                await asyncio.to_thread(shutil.rmtree, str(path), ignore_errors=False, onerror=None)
                debug(f"[batch {batch_id}] cleaned up staging area at {path}")
        except Exception as e:
            err(f"[batch {batch_id}] failed to clean up staging area at {path}: {e}")


async def rsync(batch: Batch, *, dryrun: bool = False) -> str:
    """
    RSync a file to a remote host.

    Home-relative uses normal rsync; root-relative uses sudo rsync.
    Regular files use modification time and size; templates use checksum.

    Returns a normalized message of changed files.
    """
    stag = batch.stag
    host = batch.host
    force = batch.force

    cmds = []
    if batch.has_home_relative_dsts():
        if stag.dir_home_regular:
            cmds.append(make_rsync_cmd(stag.dir_home_regular, host, root=False, checksum=False, force=force))
        if host in stag.dir_home_tpls:
            cmds.append(make_rsync_cmd(stag.dir_home_tpls[host], host, root=False, checksum=True, force=force))
    if batch.has_root_relative_dsts():
        if stag.dir_root_regular:
            cmds.append(make_rsync_cmd(stag.dir_root_regular, host, root=True, checksum=False, force=force))
        if host in stag.dir_root_tpls:
            cmds.append(make_rsync_cmd(stag.dir_root_tpls[host], host, root=True, checksum=True, force=force))

    if not cmds:
        err(f"[{batch.host}] no rsync commands to run")
        return ""

    if dryrun:
        for cmd in cmds:
            _rsync_dry(host, cmd)
            return ""

    debug(f"[{batch.host}] running {len(cmds)} rsync commands")
    msgs = await asyncio.gather(*(rsync_one(batch.host, cmd) for cmd in cmds))
    msg = normalize_msg(list(msgs))

    if msg:
        click.echo(f"[{batch.host}] {msg}")
    elif batch.verbose:
        click.echo(f"[{batch.host}] (no changes)")


def normalize_msg(msgs: list[str]) -> str:
    paths = []
    for msg in msgs:
        for line in msg.splitlines():
            for word in line.strip().split(" "):
                word = word.strip()
                if word and not word.endswith("/"):  # ignore dir info
                    if not word.startswith("/"):
                        word = f"~/{word}"  # make home-relative paths explicit
                    paths.append(word)
    return " ".join(paths)


def _rsync_dry(host: str, cmd: list[str]):
    dry(f"[{host}] {' '.join(cmd)}")


async def rsync_one(host: str, cmd: list[str]) -> str:
    try:
        debug(f"[{host}] running rsync command: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
    except FileNotFoundError:
        raise click.ClickException("rsync command not found; please install rsync to use dotsync")
    if proc.returncode != 0:
        await check_rsync_version()
        raise subprocess.CalledProcessError(proc.returncode, cmd, output=stdout, stderr=stderr)

    if not stdout:
        return ""
    return stdout.decode().strip()


def make_rsync_cmd(src_dir: Path, host: str, root: bool, checksum: bool, force: bool) -> list[str]:
    src = f"{src_dir}/"
    dst = f"{host}:{'/' if root else '~/'}"
    flags = ["-az", "--out-format=%n", "--mkpath"]
    if root:
        flags.append("--rsync-path=sudo rsync")
    if checksum and not force:
        flags.append("--checksum")
    if force:
        flags.append("--ignore-times")
    return ["rsync", *flags, "--", src, dst]


async def check_rsync_version():
    """Check that the installed rsync version is sufficient."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "rsync",
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
    except FileNotFoundError:
        raise click.ClickException("rsync command not found; please install rsync to use dotsync")

    output = stdout.decode() + stderr.decode()
    if proc.returncode == 0 and "version " in output:
        version = output.split("version ")[1].split()[0]
        major, minor, patch, *_ = (int(x) for x in version.split("."))
        if (major, minor, patch) < (3, 2, 3):
            raise click.ClickException(f"rsync version {version} is too old; please upgrade to at least 3.2.3 to use dotsync")


@dataclass
class WatchArea:
    dir: Path
    watch_to_src: dict[Path, Path]
    missing: list[Path]


async def setup_watch_area(watch_dir: Path, paths: list[Path]) -> WatchArea:
    """Set up the watch area with hard links to source files (where possible)."""
    if await watch_dir.exists():
        await asyncio.to_thread(shutil.rmtree, str(watch_dir), ignore_errors=False, onerror=None)
    await watch_dir.mkdir(parents=True)

    successful: dict[Path, Path] = dict()
    missing: list[Path] = []

    for src_path in paths:
        if not await src_path.exists():
            missing.append(src_path)
            continue
        link_path = watch_dir / mangle_name(src_path)
        await link_path.parent.mkdir(parents=True, exist_ok=True)
        if not await link_path.exists():
            try:
                os.link(src_path, link_path)
                successful[link_path] = src_path
            except OSError:
                debug(f"failed to create hard link for {src_path}")
                missing.append(src_path)

    debug(f"watch area set up at {watch_dir} with {len(successful)} links and {len(missing)} missing files: {successful}")

    return WatchArea(watch_dir, successful, missing)


def mangle_name(src_path: Path) -> str:
    """
    Mangle a source path into a single watchable filename.

    HACK: collapse the path into a single filename via hash; introduces negligible probability of collisions for material decrease in watch counts.
    """
    path_hash = hashlib.md5(str(src_path).encode()).hexdigest()[:60]
    return f"{path_hash}___{src_path.name}"


class StagingArea:
    """
    Staging area for preparing source files for sync.

    Directory structure:
    staging/
      home/
        regular/               # regular files copied here
        tpls.<host>/           # templated files for <host> rendered here
      root/
        regular/               # regular files copied here
        tpls.<host>/           # templated files for <host> rendered here
    """

    def __init__(self, base_dir: Path):
        self.dir = base_dir  # base for this staging area
        self.dir_home = self.dir / "home"
        self.dir_root = self.dir / "root"

        self.dir_home_regular: Path | None = None
        self.dir_root_regular: Path | None = None
        self.dir_home_tpls: dict[str, Path] = dict()  # host -> dir
        self.dir_root_tpls: dict[str, Path] = dict()  # host -> dir

    async def stage(self, jobs: list[Job]) -> "StagingArea":
        """Stage all jobs (regular and template) into the staging area."""
        await self.stage_regulars([j for j in jobs if not is_tpl(j.src_path)])
        await self.stage_tpls([j for j in jobs if is_tpl(j.src_path)])
        return self

    async def stage_regulars(self, jobs: list[Job]):
        for j in jobs:
            await self._stage_one_regular(j)

    async def stage_tpls(self, jobs: list[Job]):
        for j in jobs:
            await self._stage_one_tpl(j)

    async def _stage_one_regular(self, job: Job) -> Path:
        """Copy a regular source file into the staging area."""
        home, root = job.dst_relative_to(self.dir_home / "regular", self.dir_root / "regular")
        if home and not self.dir_home_regular:
            self.dir_home_regular = await (self.dir_home / "regular").resolve()
        if root and not self.dir_root_regular:
            self.dir_root_regular = await (self.dir_root / "regular").resolve()

        staged_path = home or root
        await staged_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(shutil.copy2, str(job.src_path), str(staged_path))
        return staged_path

    async def _stage_one_tpl(self, job: Job) -> Path:
        """Template then copy a source file into the staging area."""
        home, root = job.dst_relative_to(home=self.dir_home / f"tpls.{job.host}", root=self.dir_root / f"tpls.{job.host}")
        if home and job.host not in self.dir_home_tpls:
            self.dir_home_tpls[job.host] = await (self.dir_home / f"tpls.{job.host}").resolve()
        if root and job.host not in self.dir_root_tpls:
            self.dir_root_tpls[job.host] = await (self.dir_root / f"tpls.{job.host}").resolve()

        staged_path = home or root
        tpl_engine = TemplateEngine(job.vars)
        await tpl_engine.render(job.src_path, staged_path)  # mkdir handled in render
        return staged_path


async def path_if_exists(p: str) -> str | None:
    """Return path if it exists, else None."""
    return p if (await (await Path(p).expanduser()).exists()) else None


async def resolve(p: Path | str) -> Path:
    """Return resolved Path if it exists, else None."""
    return await (await Path(p).expanduser()).resolve()


def is_tpl(p: Path | str) -> bool:
    """Check if a path is a template file."""
    return Path(p).name.endswith(".tpl.j2")


def without_tpl(p: Path | str) -> Path:
    """Return path without .tpl.j2 suffix if present."""
    return Path(p).with_suffix("").with_suffix("") if is_tpl(p) else Path(p)


def tmp_prefix_uniq() -> str:
    """Generate the unique portion of a temporary directory prefix."""
    return f"{int(time.time())}-{randint(1000, 9999)}"


def err(msg: str):
    """Print error message."""
    click.echo(f"ERR: {msg}", err=True)


def warn(msg: str):
    """Print warning message."""
    click.echo(f"WARN: {msg}", err=True)


def dry(msg: str):
    """Print dry-run message."""
    click.echo(f"DRY: {msg}", err=True)


def debug(msg: str):
    """Print debug message if DOTSYNC_VERBOSE is set."""
    if DEBUG:
        click.echo(f"DEBUG: {msg}", err=True)


if __name__ == "__main__":
    cli()
