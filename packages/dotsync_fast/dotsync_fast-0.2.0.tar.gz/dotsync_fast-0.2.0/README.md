# dotsync: fast-sync to all your hosts

`dotsync` is a blazing fast CLI for syncing dotfiles to all your remote machines — **dotfiles everywhere, instantly**.

<p align="center"><img src="https://raw.githubusercontent.com/hcgatewood/dotsync/main/assets/logo.png" alt="dotsync logo" width="325"/></p>

## Features

<p align="center"><img src="https://raw.githubusercontent.com/hcgatewood/dotsync/main/assets/demo.svg" alt="dotsync demo" width="1000"/></p>

- **Concurrent smart sync** to multiple hosts over SSH — talking 100s of files to 100s of hosts
- **Just-in-time SSH** to bring your dotfiles with you wherever you SSH
- **Watch mode** for instant sync on file changes — no more manual pushes/pulls
- **Flexible configuration** with per-source and per-destination options
- **Templating support** for dynamic per-destination contents via [Jinja](https://jinja.palletsprojects.com)
- **Robust error handling** with retries and logging, and never deletes files
- **Dry-run mode** to preview sync actions without making changes

## Installation

### Homebrew

```bash
brew install hcgatewood/tap/dotsync
```

### Pip

```bash
pip install dotsync_fast
# ...and install dependencies: rsync >= 3.2.3
```

## Usage

### Initialize your config

```bash
# Create sample config file in ~/.dotsync/<hostname>.dotsync.yaml
dotsync init

# Show the materialized config file
dotsync show
```

### Quick sync

```bash
# Sync everything
dotsync

# Sync specific hosts
dotsync host1 host2

# Sync hosts by specific tags
dotsync @work @personal
```

### Watch for changes and sync automatically

```bash
# Watch and sync everything
dotsync watch

# Watch and sync specific hosts/tags
dotsync watch host1 @work
```

### SSH and bring your dotfiles with you

```bash
# Automatically sync dotfiles just-in-time on SSH
# With wildcard support, e.g. "*" for all hosts
dotsync ssh host1
````

### With templating support for per-host customizations

```bash
# Create a templated version of your dotfile, with {{ var }} placeholders
vim ~/.zshrc.tpl.j2

# Edit your config file to define the desired vars per remote host/group
dotsync edit

# Sync/watch like normal, templated files will be rendered per remote host
dotsync sync
```

## Configuration

The config is a YAML file located at `~/.dotsync/<hostname>.dotsync.yaml` or `~/.dotsync/dotsync.yaml`. The `<hostname>` is the current machine's hostname, allowing per-source-machine configurations.

```yaml
groups:
  work:
    vars: { company: pinterest }
    paths:
      /local/src: /remote/dst

hosts:
  devapp:
    tags: [ work ]              # tags organize hosts + default group-level settings
    vars: { env: production }   # vars when templating *.tpl.j2 files
    paths:
      /local/src: /remote/dst   # *.tpl.j2 src files will be templated
```

## Reference

### Top-level

```text
Usage: dotsync [OPTIONS] COMMAND [ARGS]...

  CLI for syncing dotfiles to remote hosts.

Options:
  -h, --help  Show this message and exit.

Commands:
  edit (e)   Edit dotfiles configuration file.
  init (i)   Initialize dotfiles configuration on the current machine.
  show (o)   Show dotfiles to be synced based on configuration.
  ssh (h)    SSH into a remote host configured in dotsync.
  sync (s)   Sync dotfiles to remote machines based on configuration.
  watch (w)  Watch dotfiles for changes and sync automatically.
```

### Sync and watch

```text
Usage: dotsync sync [OPTIONS] [REMOTES]...

  Sync dotfiles to remote machines based on configuration.

  REMOTES: optional list of remotes (either hostnames or @tags) to sync to; if not provided, syncs to all configured
  hosts.

Options:
  -c, --config FILE     Path to the dotsync configuration file. Defaults to searching in $DOTSYNC_CONFIG_DIR or
                        ~/.dotsync for <hostname>.dotsync.yaml then dotsync.yaml
  --src-concur INTEGER  Maximum concurrent source file syncs.  [default: 30]
  --force               Force overwrite of existing files on remote hosts.
  --dry, --dry-run      Only show what would be synced, without performing any actions.
  -v, --verbose         Enable verbose output.
  -h, --help            Show this message and exit.
```

### Turbo speed

For the fastest possible syncs (especially in `watch` mode), enable SSH connection caching in your SSH config:

```text
Host *
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h:%p
    ControlPersist 600
```

### How it works

The core of dotsync is build around efficient watching, queueing, and staging of file changes, to quickly and minimally sync changes to target hosts.

1. **File watching**: in `watch` mode, dotsync constructs an optimistic watch-layer directory of hard links to target source files, reducing the number of OS-level file watches needed; each observed change is queued to a central processing queue
2. **Change batching**: changes are batched together heuristically and as protection against rapid-fire changes; for each batch of changes, dotsync constructs a special-purpose staging-layer directory of copied/templated files to be synced

## How I use dotsync

I mainly use `dotsync` to push a subset of my personal dotfiles to our remote dev servers. With `dotsync watch`, any time I change a dotfile locally it's automatically synced to all the remote servers within a second or two, no manual work needed.

### My minimal dotsync config

```yaml
hosts:
  devapp:
    tags: [pinterest]
    paths:
      ~/.inputrc: ~/.inputrc
      ~/.profiles.remote/pinterest.bash_aliases.bash: ~/.bash_aliases
      ~/.profiles.remote/pinterest.mise.toml: ~/.mise.toml
      ~/.scripts/pbcopy_remote.py: ~/.scripts/pbcopy
```

### Setting a watch

```bash
# This gets run in a startup script on my local machine
dotsync watch @pinterest 2>&1 | tee -a "$LOGDIR/dotsync.log" &
```

## See also

- 🪄 [Kuba](https://github.com/hcgatewood/kuba): the magical kubectl companion
- 🐙 [Jdd](https://github.com/hcgatewood/jdd): JSON diff diver — the time machine for your JSON
- ☁️ [Appa](https://github.com/hcgatewood/appa): Markdown previews with live reload
- 🔮 [PDate](https://github.com/hcgatewood/pdate): human-readable dates and times
