---
title: up
layout: default
nav_enabled: true
nav_order: 1
parent: CLI
---

## `up` command

```bash
wg-qrotator up <config_file_or_interface_name>
```

Start a new rotator by providing the path to the configuration file or start an existing rotator by providing the interface's name.

Due to the secure storage of authentication cookies, to the user is always requested the password to unlock the keyring. If it is the first time a rotator is being created, extra prompts will request the creation of this password.  

### Positional arguments

- `config_file_or_interface_name` - path to the rotator's config file or, if rotator already exists, interface name.

### Options

- `-h`, `--help` - show help message

### Examples

Start a new rotator with the configuration file `rotator.yaml`:

```bash
wg-qrotator up rotator.yaml
```

Start a rotator for the interface `wg0` that was previously created:

```bash
wg-qrotator up wg0
```

