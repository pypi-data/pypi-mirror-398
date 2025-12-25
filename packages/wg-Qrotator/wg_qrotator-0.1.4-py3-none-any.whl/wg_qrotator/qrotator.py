import threading
import sys
import logging
import platform
import os
import netifaces
import signal
import keyring
from keyrings.alt.file import EncryptedKeyring

from wg_qrotator import config_parser, storage, constants
from wg_qrotator.peer import SAE, Communicator
from wg_qrotator.rotate import Rotator
from wg_qrotator.wg_key_rotation_scheduler import Key_scheduler

WG_INTERFACE = None

logger = logging.getLogger(__name__)
shutdown_event = threading.Event()
communicator = None
kr = EncryptedKeyring()
kr.keyring_key = os.environ.get("KEYRING_PASSWORD")
keyring.set_keyring(kr)

def finish() -> None:
    state = storage.Wg_qrotator_state.load()
    state.update_interface_status(WG_INTERFACE, storage.InterfaceStatus.DOWN)
    communicator.stop_listening()
    shutdown_event.set()

def handle_sigterm(signum, frame) -> None:
    """Handle SIGTERM.

    Args:
        signum (_type_): Currently ignored.
        frame (_type_): Currently ignored.
    """
    logger.info("Received termination signal, shutting down gracefully...")
    finish()

signal.signal(signal.SIGTERM, handle_sigterm)


def get_log_path(interface: str) -> str:
    """Get correct path to the rotator's log file.

    Args:
        interface (str): WireGuard interface under management.

    Returns:
        str: Log file path
    """
    system = platform.system()
    if system == "Linux":
        # Standard place for app logs
        return f"/var/log/wg_qrotator_{interface}.log"
    elif system == "Windows":
        # Common place for app logs on Windows
        log_dir = os.path.join(
            os.getenv("ProgramData", "C:\\ProgramData"), "wg_qrotator"
        )
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, f"wg_qrotator_{interface}.log")
    else:
        # Fallback for other OS (macOS, etc.)
        log_dir = os.path.expanduser("~/.wg_qrotator")
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, f"wg_qrotator_{interface}.log")


def start(config_file_path_or_interface: str) -> None:
    """Start rotator's threads and wait.

    Args:
        config_file_path_or_interface (str): Configuration file or interface name.
    """
    global WG_INTERFACE, shutdown_event, communicator

    state = storage.Wg_qrotator_state.load()

    previous_rotation_timestamp = None

    if config_file_path_or_interface in state.interfaces:
        config_file_path = state.interfaces.get(
            config_file_path_or_interface
        ).config_file
        previous_rotation_timestamp = state.interfaces.get(
            config_file_path_or_interface
        ).last_key_rotation
        state.remove_interface(config_file_path_or_interface)
    else:
        config_file_path = os.path.abspath(config_file_path_or_interface)

    config_base_dir_path = os.path.dirname(config_file_path)

    # Parse configuration file
    config = config_parser.read_config(config_file_path)

    log_path = get_log_path(config["interface"])
    logging.basicConfig(
        filename=log_path,
        level=logging.DEBUG if config.get("debug") else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    WG_INTERFACE = config["interface"]

    # Init my SAE
    my_sae = SAE(
        None,
        config.get(
            "ip", netifaces.ifaddresses(WG_INTERFACE)[netifaces.AF_INET][0]["addr"]
        ),
        config["port"],
        config["kms"]["sae"],
        (
            config["kms"]["certificate"]
            if os.path.isabs(config["kms"]["certificate"])
            else os.path.join(config_base_dir_path, config["kms"]["certificate"])
        ),
        (
            config["kms"]["secret_key"]
            if os.path.isabs(config["kms"]["secret_key"])
            else os.path.join(config_base_dir_path, config["kms"]["secret_key"])
        ),
    )

    # Init Communicator & start
    communicator = Communicator(
        my_sae.ip,
        my_sae.port,
        (
            config["secret_auth_key"]
            if os.path.isabs(config["secret_auth_key"])
            else os.path.join(config_base_dir_path, config["secret_auth_key"])
        ),
    )
    communicator.start_listening()

    state.add_interface(
        config["interface"],
        storage.WireGuardInterface(
            storage.InterfaceStatus.HOLDING,
            previous_rotation_timestamp,
            os.getpid(),
            config_file_path,
        ),
    )

    # Init & start rotator thread for each peer
    threads = []
    rotators = []
    for peer in config["peers"]:
        peer_id = list(peer.keys())[0]
        peer_info = list(peer.values())[0]
        public_auth_key_file_path = (
            peer_info["public_auth_key"]
            if os.path.isabs(peer_info["public_auth_key"])
            else os.path.join(config_base_dir_path, peer_info["public_auth_key"])
        )

        communicator.set_peer_auth_key(peer_info["ip"], public_auth_key_file_path)

        other_sae = SAE(
            peer_id,
            peer_info["ip"],
            peer_info["port"],
            peer_info["sae"],
            None,
            None,
        )
        key_scheduler = Key_scheduler(
            config["interface"],
            peer_id,
            other_sae,
            debug=config.get("debug", False),
            shutdown_event=shutdown_event,
            communicator=communicator,
            key_queue_max_size=peer_info.get("buffer_length", constants.KEY_BUFFER_SIZE),
        )
        rotator = Rotator(
            peer_info["mode"],
            config["interface"],
            my_sae,
            other_sae,
            config["kms"]["uri"],
            config["kms"]["interface"],
            (
                config["kms"]["root_certificate"]
                if os.path.isabs(config["kms"]["root_certificate"])
                else os.path.join(
                    config_base_dir_path, config["kms"]["root_certificate"]
                )
            ),
            peer_info.get("extra_handshakes", []),
            communicator,
            key_scheduler,
            debug=config.get("debug", False),
            shutdown_event=shutdown_event,
        )
        y = threading.Thread(
            target=key_scheduler.main,
        )
        y.start()
        x = threading.Thread(
            target=rotator.rotate,
        )
        x.start()
        threads.append(x)
        rotators.append(rotator)
        logger.info(f"Thread for peer {other_sae.id} has started")

    # Wait for threads to finish
    for thread in threads:
        thread.join()

    finish()

if __name__ == "__main__":
    start(sys.argv[1])
