---
title: Home
layout: home
layout: default
nav_order: 1
---

`wg-Qrotator` is a quantum-enabled hybrid key rotator for [WireGuard](https://www.wireguard.com/) IP tunnels. Following a demon-like approach, it establishes shared keys between peers using Quantum Key Distribution (QKD) and Post-Quantum Key Exchanges (PQ-KE), and periodically sets them as the underlying WireGuard tunnel Pre-Shared Key (PSK). The usage of `wg-Qrotator` introduces new security controls to ensure the forward security of WireGuard against an attacker equipped with a cryptographic-relevant quantum computer.

## What's the need of key rotation?

[NIST SP 800-57 Part 1 Rev. 5](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final) states that periodic key rotation it limits:
- the volume of data encrypted with the same key, reducing the risk of cryptanalysis;
- the potential damage if the key is exposed;
- the window of opportunity for attackers to bypass logical and physical security measures
protecting the key;
- the period within inadvertent disclosures may leak a key to unauthorized entities;
- the amount of time available for computationally intensive cryptanalysis.

## What is `wg-Qrotator` role in hardening WireGuard against the quantum computer threat?

As today, WireGuard is a very secure VPN solution, but it leverages public-key cryptographic mechanisms that are threatened by the advent of a cryptographic-relevant quantum computer. More specifically, it uses Curve25519 ECDH to establish shared keys during the periodic handshake between peers. This key exchange mechanism is impacted by the Shor's quantum algorithm that can theoretically solve the underlying mathematical problem, where the security of the algorithm resides, in polynomial time. Apart from it, it leverages symmetric cryptography that will be impacted by the Groover's quantum algorithm but it does not constitutes a vulnerability because, even with a quadratic speed up, brute force attacks are still not viable if the keys are large enough.  

We cannot say that WireGuard did not thought about this issue. Here are some words from WireGuard's [whitepaper](https://www.wireguard.com/papers/wireguard.pdf):

> While pre-sharing symmetric encryption keys is usually troublesome from a key management perspective and might be more likely stolen, the idea is that by the time quantum computing advances to break Curve25519, this pre-shared symmetric key has been long forgotten. (...)  In lieu of using a completely
post-quantum crypto system, which as of writing are not practical for use here, this optional hybrid approach of a pre-shared symmetric key to complement the elliptic curve cryptography provides a sound and acceptable trade-off for the extremely paranoid. Furthermore, it allows for building on top of WireGuard sophisticated key-rotation schemes, in order to achieve varying types of post-compromise security

Even though there's means of introducing a Pre-Shared Key (PSK) that removes the full dependency on Curve25519 ECDH, there's no means for rotating tem. That's where `wg-Qrotator` comes in, offering a non-intrusive key rotation solution that relies on QKD and PQ-KEs to periodically establish fresh shared keys relying on quantum-resistant primitives and set them as WireGuard's PSKs. Overall, hardening the tunnel's defense in depth even against quantum threats.  

