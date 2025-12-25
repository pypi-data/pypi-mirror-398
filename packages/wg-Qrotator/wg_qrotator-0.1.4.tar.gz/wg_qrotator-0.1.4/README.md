<p align="center">
<img width="208" height="70" alt="logo_with_white_text" src="https://raw.githubusercontent.com/Quantum-Communication-Group/wg-Qrotator/main/docs/assets/logo_with_white_text.png" />
</p>

`wg-Qrotator` is the quantum-enabled hybrid key rotator for [WireGuard](https://www.wireguard.com/) IP tunnels. 

Check the [documentation](https://quantum-communication-group.github.io/wg-Qrotator) for more in-depth information about the solution.

## How to set up and run
> Before starting `wg-Qrotator`, the peers must be already connected through WireGuard.

First, install the main dependencies:

```bash
sudo apt install python3 python3-pip libexplain-dev build-essential automake autoconf libtool pkg-config git
```

Then, from the root directory of the repository, install `wg-Qrotator`:

```bash
pip install wg-Qrotator
```

Next, create a `yaml` configuration file that includes information about the WireGuard network interface, the KMS and the peers.

Example of a configuration file:

```yaml
interface: wg0  # WireGuard interface to manage
port: 2345 # Port where the rotator will be exposed to its peers on the specified WireGuard's interface 
secret_auth_key: priv_auth.key # Private key used for authentication 

kms: 
  uri: "https://127.0.0.1:8443/api/v1/keys" # KMS URI
  certificate: private/certs/sae_001.crt    # SAE certificate
  root_certificate: private/certs/root.crt  # Root CA certificate
  secret_key: private/certs/sae_001.key     # SAE private key
  sae: sae_001                              # SAE ID
  interface: 14                             # KMS interface (4 for ETSI QKD 004, 14 for ETSI QKD 014)

# Information about the peers
peers:
  - 9OmSKzF5QHD5mckhBHyoN2uPPRGJNDYOl15+DKbtV1M=: # ID (public key) of the peer
      public_auth_key: pub_auth_0.key # Peer public key used for authentication 
      ip: 10.0.0.2                    # IP of the peer
      port: 2347                      # Port of the peer rotator
      sae: sae_002                    # SAE of the peer in the KMS
      mode: client                    # Mode (client/server)
      extra_handshakes:               # PQ extra handshakes
      - ML_KEM_1024:                  # KEM to use in PQ-KE
  - 12mSKzF5QHd57ckhBHyoN2uPPRGJNDYOl15+dfbt19L=: # Another peer...
      public_auth_key: pub_auth_1.key
      ip: 10.0.0.3
      port: 3456
      sae: sae_003
      mode: server
```

Note that each entity that participates must be registered in the KMS and the certificate and keys must be set up for the requests to be made. Also, make sure that the IPs that are being used are the ones that point to WireGuard's interface, this way all the communications will go through the already established secure tunnel.

The `mode` tells the role for this rotator when interacting with a given peer. The *client* is the initiator, and the *server* will only act upon the *client*'s request. Note that the indicated `mode` is the one used by the entity that uses this configuration file, for the other peer it shall be the opposite. 

To generate the authentication key for each rotator, use the `genauthkeys` command as in the following example:

```bash
wg-qrotator genauthkeys priv_auth.key pub_auth.key
```

Start the rotator on each peer by running:

```bash
wg-qrotator up <config.yaml>
```

Note that `sudo` privileges might be needed in order to monitor and update WireGuards PSKs.

A log file is stored in the default logs directory (e.g. `/var/log/` for Linux) under the name `wg_qrotator_<wg_interface>.log`.

## Key combination

There is the possibility to add key exchanges and use their respective resulting keys in the key combination process. The final pre-shared key will be the OTP of the key given by the KMS and all the other keys extracted from extra key exchanges. 

To activate extra key exchanges just add the field `extra_handshakes` for a given peer and enumerate the name of the exchanges to be used. For example:

```yaml
...
peers:
  - 9OmSKzF5QHD5mckhBHyoN2uPPRGJNDYOl15+DKbtV1M=: 
      ...
      extra_handshakes:
        - ML_KEM_512:
        - ...
```

The following key exchanges are supported:

- `ML_KEM_512`
- `ML_KEM_768`
- `ML_KEM_1024`

# License

© 2025, IT - Instituto de Telecomunicações

This project is licensed under the [GNU Affero General Public License v3.0](https://www.gnu.org/licenses/agpl-3.0.en.html).

# Acknowledgements

This project was supported by:
- the members of the NATO STO IST-218 RTG with title “Multi-Domain Quantum Key Distribution (QKD) for Military Usage”;
- the NATO Emerging Security Challenges Division through the Science for Peace and Security (SPS) programme under the project QSCAN reference: G6158-MYP;
- the European Union’s Horizon Europe research and innovation programme under the project "Quantum Secure Networks Partnership" (QSNP, grant agreement No 101114043).