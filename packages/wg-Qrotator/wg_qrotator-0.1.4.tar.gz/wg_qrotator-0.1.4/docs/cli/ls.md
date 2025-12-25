---
title: ls
layout: default
nav_enabled: true
nav_order: 4
parent: CLI
---

## `ls` command

```bash
wg-qrotator ls
```

List all rotators. Output includes the interface name, the status, and the timestamp of the last key rotation.

In the current implementation, a rotator can be in one of the following three states:
- `down` - the rotator was created, but it is not running.
- `hold` - the rotator is waiting or during the bootstrap phase.
- `up` - the rotator is up and running.

The granularity of this command stop at the network interface. This means that it does not show the state or the timestamp of the last key rotation for each peer inside a single rotator. Please check the rotator's logs for more information.

### Positional arguments

None.

### Options

- `-h`, `--help` - show help message

### Examples

```bash
$ wg-qrotator ls
Interface  Status  Last Key Rotation         
---------------------------------------------
wg0        up      2025-09-30T11:25:18.175369
wg1        down    2025-09-29T19:24:11.543578
```