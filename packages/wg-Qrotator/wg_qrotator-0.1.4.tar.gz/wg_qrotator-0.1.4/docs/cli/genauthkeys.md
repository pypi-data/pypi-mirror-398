---
title: genauthkeys
layout: default
nav_enabled: true
nav_order: 6
parent: CLI
---

## `genauthkeys` command

```bash
wg-qrotator genauthkeys <private_file_path> <public_file_path>
```

Generate ML-DSA-87 key-pair.

### Positional arguments

- `private_file_path` - path to the file where the private key will be stored
- `public_file_path` - path to the file where the public key will be stored

### Options

- `-h`, `--help` - show help message

### Examples

Generate authentication key pair and store the private key in `priv.key` and the public key in `pub.key`:

```bash
wg-qrotator genauthkeys priv.key pub.key
```