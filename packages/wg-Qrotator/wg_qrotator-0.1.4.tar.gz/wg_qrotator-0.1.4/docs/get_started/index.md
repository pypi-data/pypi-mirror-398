---
title: Get started
layout: default
nav_enabled: true
nav_order: 2
---

# Get started

To get started with `wg-Qrotator`:
1. make sure the host machine meets the [requiremets](/wg-Qrotator/get_started/requirements.html);
2. perform the [installation](/wg-Qrotator/get_started/installation.html);
3. deploy your first rotator by checking how to [create a key rotator](/wg-Qrotator/get_started/create_a_key_rotator.html) and this [example](/wg-Qrotator/get_started/example.html).

Notice that `wg-Qrotator` was developed to be deployed in a QKD Network, and it requires access to a QKD Node Key Management System (KMS) in order to retrieve quantum-generated keys. The key rotator can have direct access to a QKD Module, but it limits the reachability of each key rotator, since each QKD Module usually it only establishes one link. 