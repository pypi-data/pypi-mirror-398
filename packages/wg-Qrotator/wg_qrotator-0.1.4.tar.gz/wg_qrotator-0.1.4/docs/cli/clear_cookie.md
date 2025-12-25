---
title: clearcookie
layout: default
nav_enabled: true
nav_order: 5
parent: CLI
---

## `clearcookie` command

```bash
wg-qrotator clearcookie <interface_name> <peer_ip>
```

Delete the stored cookie for a given peer. This can be used to solve messages being dropped due to NONCE checks. If this is performed for a given peer, the same action must be performed also in the peer's rotator.

### Positional arguments

- `interface_name`- interface to clear cookie
- `peer_ip` - IP address of the peer to clear cookie

### Options

- `-h`, `--help` - show help message

### Examples

Clear the cookie for the peer in the `wg0` interface with IP equal to 10.0.0.2:
```bash
wg-qrotator clearcookie wg0 10.0.0.2
```
