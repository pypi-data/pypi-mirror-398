---
title: down
layout: default
nav_enabled: true
nav_order: 2
parent: CLI
---

## `down` command

```bash
wg-qrotator down <interface_name>
```

Stop an existing rotator by providing the interface's name.

### Positional arguments

- `interface` - name of the WireGuard interface managed by the rotator to be stopped

### Options

- `-h`, `--help` - show help message

### Examples

Stop a rotator for the interface `wg0` that was previously started:

```bash
wg-qrotator down wg0
```