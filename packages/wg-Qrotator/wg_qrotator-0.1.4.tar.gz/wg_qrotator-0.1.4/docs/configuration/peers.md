---
title: Peers
layout: default
parent: Configuration
nav_order: 3
---

## Peers configuration

Each active rotator is able to manage one or more tunnels within the same network interface. Nonetheless, at each end of a tunnel, one rotator must be active. Key rotators establish shared keys between key for each tunnel under management. Their communications need to be carried out within an already established secure channel. 

```yaml
peers:
  - <peer_wg_pub_key>:
      ip: <peer_rotator_ip>
      port: <peer_rotator_port>
      sae: <peer_sae>
      public_auth_key: <peer_rotator_public_authentication_key_file>
      mode: [client | server]
      buffer_length: <buffer_length>
      extra_handshakes:
      - <algorithm_id>:  
          secret_key: <secret_key_file>
          public_key: <peer_public_key_file>
```

### `peers.<peer_wg_pub_key>`

Peer configuration. The value `<peer_wg_pub_key>` is the peer's WireGuard public key. 

### `peers.<peer_wg_pub_key>.ip` - `str`

IP address where the peer's rotator is exposed.

### `peers.<peer_wg_pub_key>.port` - `int`

Port number where the peer's rotator is exposed.

### `peers.<peer_wg_pub_key>.sae` - `str`

Peer's Secure Application Entity (SAE) identifier. This value is used for the rotator to identify the peer towards the KMS. 

### `peers.<public_auth_key>` - `str`

Path to the file containing the peer's rotator ML-DSA-87 public key used for authentication.

### `peers.<peer_wg_pub_key>.mode` - `str`

Operation mode of the rotator when interacting with its peer. It accepts:
- `client` - it starts all the stages in the protocol.
- `server` - it has a reactive behavior to the client's signals.

Note that, between two rotators, one must have the `client` role and the other the `server` role.

### `buffer_length` - `int` - `optional`

Length of the internal key buffer. Accept an integer between 1 and 32. Defaults to 3.

If two peers have set two different values, the rotator will be shutdown.

### `peers.<peer_wg_pub_key>.extra_handshakes` - `[str]` - `optional` 

List of PQ-KEs to be used.

Identifier of the KEM to be used in the extra key exchange. It accepts:
- `ML_KEM_512`
- `ML_KEM_768`
- `ML_KEM_1024`

The definition of `extra_handshakes` is optional.

If two peers have set two different values, the rotator will be shutdown.
