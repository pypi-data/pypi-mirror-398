---
title: Security considerations
layout: default
nav_enabled: true
nav_order: 6
---

# Security Consideration

{: .disclaimer }
No security guarantees are provided by the creators, maintainers, contributors, and respective organizations. Perform an always advised risk assessment before deploying it in a production environment. `wg-Qrotator` is distributed under the AGPLv3 license.

## Communication security between rotators

As mentioned multiple times within this documentation, peer rotators must communicate through an already established secure communication channel. For a lot of solutions this would be a serious deployment headache, but in our scenario is not since `wg-Qrotator` only makes sense to be deployed if a tunnel established by WireGuard already exists. A rotator should be exposed on the host IP inside the respective WireGuard VPN - this is the default behavior. If a PSK is set during the setup of the tunnel, the risk imposed by the quantum threat is mitigated from the beginning. 

Nonetheless, this approach only provides guarantees against a third-party (Eve) but not against attacks originated by different users within the same host where the rotator is deployed. This is due to the fact that any program inside the host most likely will be able to communicate through the network interfaces managed by WireGuard. Consequently, an authentication mechanism based on a 32 byte cookie stored in an encrypted file at each host was introduced. Each tunnel rotated by `wg_Qrotator` has its own cookie that is shared with the respective peer. Cookies are generated from the generated keys and are used to generate an authenticated MAC that is introduced in every message sent and verified by the peer. This introduces the need for a password to encrypt the file where the keys are stored. For the first messages that are interchanged, since there's not yet a shared secret to build the cookie from, a post-quantum digital signature algorithm is used. ML-DSA is leveraged with the keys provided in the configuration file under `secret_auth_key` and `public_auth_key`. Also, at the user's risk, the cookie storage can be populated beforehand, check [keyring](https://pypi.org/project/keyring/) and [keyring.alt](https://pypi.org/project/keyrings.alt/). As an example, the cookie for the peer with IP equal to `10.0.0.2` in the `wg0` interface is stored in the keyring with `service_name = "wg-qrotator"` and `user = "wg0_10.0.0.2"`.

## Ephemeral keys

To ensure Perfect Forward Secrecy (PFS), for each PQ-KE an ephemeral key-pair is generated for each peer. Since the communication channel is authenticated, this comes with no security impact, and also reduces the configuration overhead simplifying the user experience.

## Logs

Currently, by setting the `debug` parameter in the configuration file to `true` will trigger each generated key to be logged in plaintext, use this only for testing. Also, there's no mechanism in place to limit the size of the log files. 


