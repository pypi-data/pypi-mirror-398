---
title: General
layout: default
parent: Configuration
nav_order: 1
---

## General configuration

In this section of the configuration file, local-only parameters are defined.

```yaml
interface: <wireguard_network_interface>
port: <rotator_port_number>
secret_auth_key: <rotator_private_authentication_key_file>
ip: <rotator_ip_address>
debug: [true | false]
```

### `interface` - `str`

WireGuard network interface where the rotator will take effect.

### `port` - `int`

Port number where the rotator will be exposed.

### `secret_auth_key` - `str`

Path to the file containing the rotator ML-DSA-87 private key used for authentication.

### `ip` - `str` - `optional` 

Optional IP address where the rotator will be exposed. By default, it will be used the IP assigned to the interface indicated in `interface` field.

### `debug` - `bool` - `optional` 

Optional debug flag. Defaults to `false`.

{: .tip }
Each rotator writes to the OS's default log directory in a file names `wg_qrotator_<interface_name>.log`. For example, in a Linux machine, a rotator managing `wg0` writes its logs to `/var/log/wg_qrotator_wg0.log`.

