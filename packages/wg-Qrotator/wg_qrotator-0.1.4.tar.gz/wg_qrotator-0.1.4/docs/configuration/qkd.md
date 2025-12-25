---
title: QKD
layout: default
parent: Configuration
nav_order: 2
---

## Quantum Key Distribution key source configuration

The main source of key for `wg-Qrotator` to establish new keys for rotation is Quantum Key Distribution (QKD). Actually, a QKD key source is mandatory for the rotator to work. Keys are retrieved from the node's Key Management System (KMS) or directly from a QKD Module. 

```yml
kms: 
  uri: <kms_location>
  interface: [4 | 14]
  sae: <SAE_ID>
  certificate: <SAE_certificate_file>
  secret_key: <SAE_secret_key_file>
  root_certificate: <root_CA_certificate_file>
```

### `kms.uri` - `str`

Location of the KMS to retrieve keys. If the KMS exposes the ETSI GS QKD 004 interface, just input the IP and port of the KMS (e.g. `192.168.1.200:3237`). If the ETSI GS QKD is being used, input the full URL of the `/keys` endpoint (e.g. `https://192.168.1.200/api/v1/keys`).

### `kms.interface` - `int`

Interface standard exposed by the KMS. The valid values are:
- `4` - for ETSI GS QKD 004;
- `14` - for ETSI GS QKD 014;

### `kms.sae` - `str`

Secure Application Entity (SAE) identifier. This value is used for the rotator to identify itself towards the KMS. 

### `certificate` - `str`

Path to the file containing the certificate to be used to authenticate the rotator towards the KMS.

### `secret_key` - `str`

Path to the file containing the private key to be used when interacting the KMS. 

### `root_certificate` - `str`

Path to the file containing the certificate of the root CA in order to validate the KMS's identity.

