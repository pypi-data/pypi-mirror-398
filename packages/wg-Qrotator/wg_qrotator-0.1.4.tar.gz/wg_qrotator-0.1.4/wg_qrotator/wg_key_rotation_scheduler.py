import subprocess
import os
import time
import traceback
import logging
import base64
from queue import Queue

from wg_qrotator import storage

logger = logging.getLogger(__name__)


class Key_scheduler:
    def __init__(
        self,
        wg_interface: str,
        wg_peer_id: str,
        other_sae,
        key_queue_max_size=3,
        debug=False,
        shutdown_event=None,
        communicator=None,
    ):
        self.wg_interface = wg_interface
        self.wg_peer_id = wg_peer_id
        self.key_queue_max_size = key_queue_max_size
        self.key_buffer = Queue(maxsize=key_queue_max_size)
        self.debug = debug
        self.shutdown_event = shutdown_event
        self.storage = storage.Wg_qrotator_state.load()
        self.communicator = communicator
        self.other_sae = other_sae
        self.halt = False

    def update_psk(self, key) -> bool:
        """Rotate WireGuard's tunnel PSK.

        Args:
            key (str|bytes): Base64 formatted key to be set as PSK.

        Returns:
            bool: Success status.
        """
        if self.drop_current_key:
            self.drop_current_key = False
            return False

        if self.debug:
            logger.debug(f"PSK -> {key}")

        peer_id_bytes = self.wg_peer_id.encode("utf-8")
        safe_peer_id = base64.urlsafe_b64encode(peer_id_bytes).decode("ascii")
        # Store the key in a file
        if type(key) == bytes:
            with open(f"k{safe_peer_id}.key", "wb+") as f:
                f.write(key)
        else:
            with open(f"k{safe_peer_id}.key", "w+") as f:
                f.write(key)

        # Set PSK
        result = None
        if self.communicator.send_ping(self.other_sae.ip, self.other_sae.port):
            result = subprocess.run(
                f"wg set {self.wg_interface} peer {self.wg_peer_id} preshared-key k{safe_peer_id}.key",
                shell=True,
            )
            if result.returncode == 0:
                self.storage.update_rotation_timestamp(self.wg_interface)

        # Delete file
        os.remove(f"k{safe_peer_id}.key")

        return False if not result or result.returncode != 0 else True

    def reset_key_buffer(self) -> None:
        """Clear shared key buffer."""
        while not self.key_buffer.empty():
            _ = self.key_buffer.get()
        self.drop_current_key = True

    def last_handshake_epoch(self) -> int:
        """Find the timestamp of the last WireGuard's tunnel handshake.

        Returns:
            int: Timestamp of the last handshake.
        """
        # Get the latest handshake epoch using the wg show command
        result = subprocess.run(
            f"wg show {self.wg_interface} latest-handshakes",
            shell=True,
            capture_output=True,
        ).stdout.decode()

        if result:
            lines = result.split("\n")
            for line in lines:
                if len(line) != 0:
                    splitted_line = line.split("\t")
                    peer_id = splitted_line[0].strip()
                    last_handshake_epoch = splitted_line[1].strip()
                    if peer_id == self.wg_peer_id:
                        return int(last_handshake_epoch)
        else:
            return 0

    def main(self) -> None:
        """Key rotation scheduler main workflow."""
        while not self.shutdown_event.is_set():
            if self.halt:
                time.sleep(1)
                continue

            # Get a key from the key buffer (blocking)
            try:
                psk = self.key_buffer.get(timeout=10)
                self.drop_current_key = False
            except:
                continue

            # Wait for the right time to rotate the key
            while not self.drop_current_key and not self.shutdown_event.is_set():
                try:
                    seconds_since_last_handshake = (
                        int(time.time()) - self.last_handshake_epoch()
                    )

                    if seconds_since_last_handshake < 30:
                        if self.update_psk(psk):
                            logger.info(f"Key rotated at {time.ctime()}")
                        else:
                            logger.error("Unable to rotate key.")
                        time.sleep(30)
                        break

                    time.sleep(5)
                except:
                    tb_str = traceback.format_exc()
                    time.sleep(10)
                    logger.error(
                        f"Unable to retrieve underlying tunnel handshake information: {tb_str}"
                    )
