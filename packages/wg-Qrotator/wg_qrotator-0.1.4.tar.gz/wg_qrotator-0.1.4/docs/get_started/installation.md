---
title: Installation
layout: default
nav_enabled: true
nav_order: 2
parent: Get started
---

## Installation

### Using `pip`

Install `wg-Qrotator` using the `pip` command:

```bash
pip install wg-Qrotator
```

If the installation finishes with success, the `wg-qrotator` command should now be available.

If the `pip install wg-Qrotator` fails, try updating `pip`:

```bash
pip install --upgrade pip
```

If the problem persists, check if all requirements are met.

### Using `pipx`

Installing Python packages system-wide is not recommended. [pipx]("https://github.com/pypa/pipx") solves this problem by automatically installing Python packages on a isolated environment.

Fist ensure `pipx` is installed:

```bash
apt install pipx
```

Next install `wg-Qrotator`:

```bash
pipx install wg-Qrotator
```

## Post-installation

For a rotator to work as expected, it needs enough privileges to manage WireGuard. That means that a simple user will most likely not be able to start a rotator that works correctly. 

To check if the user where wg-Qrotator was installed has enough privileges, try running the following command (even if a tunnel named `wg0` does not exist):

```bash
wg show wg0
```

If the output does not mention `Operation not permitted`, you're good to go. If it does, there's two main options to fix this issue:
1. Update sudoers PATH to include wg-Qrotator.
2. Install wg-Qrotator on root or using sudo;

### 1st option - Update sudoers PATH to include wg-Qrotator

Both `pip` and `pipx` commonly save the executable for the CLI at `/home/<user_name>/.local/bin/`.

To run the `wg-Qrotator` with `sudo`, add `/home/<user_name>/.local/bin` to `sudo`'s PATH by running `sudo visudo` and appending `:/home/<your_username>/.local/bin` to the string in the line with the following format `Defaults        secure_path="...`. 

For example, if the user name where wg-Qrotator is installed is `john`, then the content of that line will most likely be:
```
Defaults        secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin:/home/john/.local/bin"
```

Then, if wg-Qrotator was installed using `pip`, it can be run by executing:
```bash
sudo -E wg-qrotator ...
```

If it was installed using `pipx`, it can be run by executing:
```bash
sudo wg-qrotator ...
```

### 2nd option - Install wg-Qrotator on root or using sudo (not recommended)

Just run the installation commands presented before with sudo or directly as root.
