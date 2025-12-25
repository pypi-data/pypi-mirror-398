---
title: rm
layout: default
nav_enabled: true
nav_order: 3
parent: CLI
---

## `rm` command

```bash
wg-qrotator rm <interface_name>
```

Removes the rotator attached to the indicated interface from the internal state storage.  

### Positional arguments

- `interface` - name of the WireGuard interface managed by the rotator to be removed

### Options

- `-h`, `--help` -  show help message.
- `-f`, `--force` - force the removal of the rotator. It bypasses the need of a successful rotator's configuration file check and cookie removal. 

### Examples

Remove the rotator that managed the `wg0` interface:

```bash
wg-qrotator rm wg0
```


