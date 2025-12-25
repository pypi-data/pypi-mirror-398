import tempfile
import base64
import time
import datetime
import logging
import keyring
import traceback
import binascii
import os

from datetime import timezone
from hashlib import sha256, sha512
from filelock import FileLock

from wg_qrotator import handshake, kms, storage, constants

from wg_qrotator.peer import SAE, Communicator
from wg_qrotator.wg_key_rotation_scheduler import Key_scheduler
import wg_qrotator.exceptions as e

logger = logging.getLogger(__name__)


LOCK_PATH = os.environ.get("WG_QROTATOR_KEYRING_LOCK") or os.path.join(
    tempfile.gettempdir(), "wg_qrotator_keyring.lock"
)
lock = FileLock(LOCK_PATH)


class Rotator:
    def __init__(
        self,
        mode: str,
        wg_int: str,
        my_sae: SAE,
        other_sae: SAE,
        kms_uri: str,
        kms_interface: int,
        root_crt: str,
        extra_handshakes: list,
        communicator: Communicator,
        key_scheduler: Key_scheduler,
        shutdown_event=None,
        debug: bool = False,
    ) -> None:
        self.mode = mode
        self.my_sae = my_sae
        self.other_sae = other_sae
        self.kms_uri = kms_uri
        self.communicator = communicator
        self.start_at = None
        self.root_crt = root_crt
        self.wg_interface = wg_int
        self.extra_handshakes = extra_handshakes
        self.kms_interface = kms_interface
        self.rotation_counter = 0
        if self.kms_interface == 4:
            self.kms = None
        elif self.kms_interface == 14:
            self.kms = kms.ETSI_014(kms_uri, root_crt, my_sae, other_sae)
        else:
            raise e.KMS_exception(f"Invalid interface: {self.kms_interface}")
        self.key_scheduler = key_scheduler
        self.debug = debug
        self.finish = False
        self.storage = storage.Wg_qrotator_state.load()
        self.shutdown_event = shutdown_event

    def __clear(self) -> None:
        """Close key streams."""
        if self.kms_interface == 4 and self.kms.ksid:
            self.kms.close()
        self.key_scheduler.drop_current_key = True

    def __update_rotation_counter(self) -> None:
        """Increment total rotation counter."""
        self.rotation_counter = (self.rotation_counter + 1) % (2**16 - 1)

    def __compute_key_hash(
        self, key: bytes | str, salt: bytes, return_bytes=False, use_sha_512=False
    ) -> str | bytes:
        """Calculate hash.

        Args:
            key (bytes | str): Value to be hashed.
            salt (bytes): Salt.

        Returns:
            str | bytes: Hash value.
        """
        if not isinstance(key, bytes):
            key = key.encode()
        if use_sha_512:
            h = sha512(key)
        else:
            h = sha256(key)
        h.update(salt)
        return h.digest() if return_bytes else h.hexdigest()

    def __do_extra_handshakes(self, key: str) -> bytes:
        """Rotator's PQ key exchanges workflow.

        Args:
            key (str): Base key to be combined with.

        Returns:
            str: Final key after key exchanges.
        """
        if not self.extra_handshakes:
            return key
        st = time.time()
        other_key = handshake.handshake(
            self.extra_handshakes, self.mode, self.communicator, self.other_sae
        )
        if not other_key:
            logger.error(f"Error during extra handshakes with {self.other_sae.id}")
            return key
        logger.debug(f"PQ key -> {base64.b64encode(other_key).decode()}")
        final_bytes = bytes(x ^ y for x, y in zip(base64.b64decode(key), other_key))

        print(time.time() - st)

        return base64.b64encode(final_bytes).decode()

    def __ack(self, msg_id: int) -> None:
        """Send acknowledgement message.

        Args:
            msg_id (int): Identifier of the message to the acknowledged.
        """
        self.communicator.send_message(
            {"msg_type": "Ack", "acked": msg_id},
            self.other_sae.ip,
            self.other_sae.port,
        )

    def __update_cookie(
        self, cookie: bytes, persist: bool = True, set_in_communicator: bool = True
    ) -> None:
        """Update peer cookie in the keyring and set it in the Communicator

        Args:
            cookie (bytes): cookie (32 bytes)
        """
        if set_in_communicator:
            current_cookie = self.communicator.get_peer_cookie(self.other_sae.ip)
            if current_cookie is not None:
                self.communicator.set_peer_back_cookie(
                    self.other_sae.ip, current_cookie
                )
            self.communicator.set_peer_cookie(self.other_sae.ip, cookie)

        if persist:
            salt = (
                self.my_sae.sae_id.encode() + self.other_sae.sae_id.encode()
                if self.mode == "server"
                else self.other_sae.sae_id.encode() + self.my_sae.sae_id.encode()
            )
            hello_cookie = self.__compute_key_hash(cookie, salt, return_bytes=True)
            self.communicator.set_peer_hello_cookie(self.other_sae.ip, hello_cookie)
            with lock:
                keyring.set_password(
                    "wg_qrotator",
                    f"{self.wg_interface}_{self.other_sae.ip}",
                    base64.b64encode(cookie).decode("utf-8"),
                )

    def abort(self) -> None:
        """Send key rotation abort message."""
        self.communicator.send_message(
            {
                "msg_type": "Abort round",
            },
            self.other_sae.ip,
            self.other_sae.port,
        )

    def __get_cookie(self) -> bytes:
        """Get cookie (32 bytes) or return zeroed cookie."""
        val = keyring.get_password(
            "wg_qrotator", f"{self.wg_interface}_{self.other_sae.ip}"
        )
        if not val:
            return None
        try:
            cookie = base64.b64decode(val, validate=True)
        except (TypeError, binascii.Error) as err:
            logger.warning("Stored cookie is invalid base64; reinitializing. %s", err)
            return bytes(32)
        if len(cookie) != 32:
            logger.warning(
                "Stored cookie has invalid length %d; expected 32", len(cookie)
            )
            return bytes(32)
        return cookie

    # Hello & synch messages
    def initial_workflow(self) -> None:
        """Rotator's bootstrap workflow."""
        self.key_scheduler.halt = True
        auth_cookie = self.__get_cookie()
        if auth_cookie is None:
            logger.info(f"Using ML-DSA authentication")
            self.communicator.set_use_dsa(self.other_sae.ip, True)
        else:
            self.communicator.set_peer_cookie(self.other_sae.ip, auth_cookie)
            self.communicator.set_peer_hello_cookie(self.other_sae.ip, auth_cookie)
        self.rotation_counter = 0
        self.key_scheduler.reset_key_buffer()
        if self.mode == "client":
            # Send hello msg & wait for ack
            while not self.shutdown_event.is_set():
                try:
                    current_time = datetime.datetime.now(timezone.utc)
                    start_time = current_time + datetime.timedelta(seconds=20)
                    start_time = start_time.replace(microsecond=0)
                    self.communicator.send_message(
                        {
                            "msg_type": "Hello",
                            "start_at": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "kems": self.extra_handshakes,
                            "key_buffer_length": self.key_scheduler.key_queue_max_size,
                        },
                        self.other_sae.ip,
                        self.other_sae.port,
                        wait_for_ack=True,
                    )
                    break
                except e.Connection_timeout:
                    self.start_at = None
                    pass

            if self.shutdown_event.is_set():
                return

            if self.kms_interface == 4:
                self.kms = kms.ETSI_004(
                    self.kms_uri, self.root_crt, self.my_sae, self.other_sae
                )

            self.start_at = start_time.replace(tzinfo=None)
            logger.info(f"Starting at {self.start_at}")
        else:
            # Receive hello msg
            msg = None
            while not self.shutdown_event.is_set():
                try:
                    msg = self.communicator.wait_for_message(
                        1, 5, self.other_sae.ip, message_types=["Hello"]
                    )
                    break
                except e.Connection_timeout:
                    pass

            if not msg or self.shutdown_event.is_set():
                self.start_at = None
                return

            if msg.get("kems") != self.extra_handshakes:
                logger.error(
                    f"PQ-KE KEMs selection does not match. Rotator cannot be started for {self.other_sae.id}"
                )
                self.abort()
                raise e.Initial_workflow_exception(f"KEMs selection did not match for {self.other_sae.id}")

            if msg.get("key_buffer_length", constants.KEY_BUFFER_SIZE) != self.key_scheduler.key_queue_max_size:
                logger.error(
                    f"Selected key buffer length does not match. Rotator cannot be started for {self.other_sae.id}"
                )
                self.abort()
                raise e.Initial_workflow_exception(f"Key buffer length did not match for {self.other_sae.id}")

            # Ack hello msg
            self.__ack(msg["msg_id"])

            if self.kms_interface == 4:
                self.kms = kms.ETSI_004(
                    self.kms_uri,
                    self.root_crt,
                    self.my_sae,
                    self.other_sae,
                    inverted=True,
                )

            self.start_at = datetime.datetime.strptime(
                msg["start_at"], "%Y-%m-%d %H:%M:%S"
            )
            logger.info(f"Starting at {self.start_at}")

    def client_rotation(self) -> None:
        """Client's rotation workflow."""
        # Get a key from the KMS
        try:
            key, key_id = self.kms.get_key()
        except ValueError as err:
            logger.error(f"GET KEY failed - {self.other_sae.id}:\n{err}")
            self.abort()
            return

        logger.debug(f"KMS -> {key}")

        # Send the key id to the peer
        msg_id = self.communicator.send_message(
            {
                "msg_type": "Rotate",
                "key_id": key_id,
            },
            self.other_sae.ip,
            self.other_sae.port,
        )

        # Wait for ack
        self.communicator.wait_for_ack(
            constants.LISTEN_TRIES_PERIOD,
            constants.LISTEN_TIMEOUT_TRIES,
            msg_id,
            self.other_sae.ip,
        )

        # Optional key exchanges
        key = self.__do_extra_handshakes(key)

        # Compute and send to peer the hash of the final key
        key_hash = self.__compute_key_hash(
            key,
            self.my_sae.sae_id.encode()
            + self.other_sae.sae_id.encode()
            + str(self.rotation_counter).encode(),
            use_sha_512=True,
        )

        self.communicator.send_message(
            {
                "msg_type": "Key_hash",
                "hash": key_hash,
            },
            self.other_sae.ip,
            self.other_sae.port,
            wait_for_ack=True,
        )

        logger.debug(f"New key -> {key}")

        # Store the new key in the key queue
        self.key_scheduler.key_buffer.put(key)

        new_cookie = self.__compute_key_hash(
            key, f"{self.rotation_counter}".encode(), return_bytes=True
        )

        self.__update_cookie(
            new_cookie,
            set_in_communicator=self.rotation_counter % constants.KEY_BUFFER_SIZE == 0,
        )
        if self.rotation_counter == 0:
            self.communicator.set_use_dsa(self.other_sae.ip, False)
            self.key_scheduler.halt = False
            time.sleep(5)
        self.__update_rotation_counter()

    def server_rotation(self) -> None:
        """Server's rotation workflow."""
        # Wait for rotation request from the peer (i.e. the client)
        while not self.shutdown_event.is_set():
            try:
                msg = self.communicator.wait_for_message(
                    constants.LISTEN_TRIES_PERIOD,
                    constants.LISTEN_TIMEOUT_TRIES / 10,
                    self.other_sae.ip,
                    message_types=["Rotate", "Hello"],
                )
                break
            except:
                pass
        if self.shutdown_event.is_set():
            return

        # If Hello message was received, it means that the peer has restarted
        if msg["msg_type"] == "Hello":
            self.start_at = None
            self.__clear()
            return
        key_id = msg.get("key_id")

        if key_id is None:
            traceback.print_exc()
            logger.error(
                f"Error during key rotation with {self.other_sae.id}",
            )
            return

        # Get key from the KMS
        try:
            key, key_id = self.kms.get_key(key_id)
        except ValueError as err:
            logger.error(
                f"GET KEY failed - {self.other_sae.id}:\n{err}",
            )
            self.abort()
            return

        logger.debug(f"KMS -> {key}")

        # Ack
        self.__ack(msg["msg_id"])

        # Optional key exchanges
        key = self.__do_extra_handshakes(key)

        msg = self.communicator.wait_for_message(
            constants.LISTEN_TRIES_PERIOD,
            constants.LISTEN_TIMEOUT_TRIES,
            self.other_sae.ip,
            message_types=["Key_hash"],
        )
        peer_key_hash = msg.get("hash")

        key_hash = self.__compute_key_hash(
            key,
            self.other_sae.sae_id.encode()
            + self.my_sae.sae_id.encode()
            + str(self.rotation_counter).encode(),
            use_sha_512=True,
        )

        # Check if hashes match
        if peer_key_hash == key_hash:
            self.__ack(msg["msg_id"])

            logger.debug(f"New key -> {key}")
            # Store the new key in the key queue
            self.key_scheduler.key_buffer.put(key)

            new_cookie = self.__compute_key_hash(
                key,
                f"{self.rotation_counter}".encode(),
                return_bytes=True,
            )
            self.__update_cookie(
                new_cookie,
                set_in_communicator=self.rotation_counter % constants.KEY_BUFFER_SIZE
                == 0,
            )
            if self.rotation_counter == 0:
                self.communicator.set_use_dsa(self.other_sae.ip, False)
                self.key_scheduler.halt = False
                time.sleep(5)
            self.__update_rotation_counter()
        else:
            logger.error(
                f"Error during key rotation hash check with {self.other_sae.id}"
            )

    def rotate(self) -> None:
        """Key rotator main."""
        while not self.finish and not self.shutdown_event.is_set():
            try:
                if not self.start_at:
                    self.storage.update_interface_status(
                        self.wg_interface, storage.InterfaceStatus.HOLDING
                    )
                    # Initial workflow: hello and synch
                    try:
                        self.initial_workflow()
                    except e.Initial_workflow_exception:
                        logger.info(f"Rotator for {self.other_sae.id} has finished due to an error in the initial peer handshake")
                        return                 
                    # Wait until start_at
                    if self.start_at:
                        time_difference = (
                            self.start_at
                            - datetime.datetime.now(timezone.utc).replace(tzinfo=None)
                        ).total_seconds()
                        time.sleep(time_difference)

                        self.storage.update_interface_status(
                            self.wg_interface, storage.InterfaceStatus.UP
                        )
                    else:
                        continue

                # Server listen right away
                if self.mode == "server":
                    self.server_rotation()
                else:
                    # Client waits until there's space in the key queue (buffer)
                    if not self.key_scheduler.key_buffer.full():
                        self.client_rotation()
                    else:
                        time.sleep(1)
                        continue
            except e.Connection_timeout:
                self.start_at = None
                self.__clear()
            except:
                logger.exception("Rotation round aborted with %s", self.other_sae.id)
                time.sleep(1)
                continue

        if self.finish or self.shutdown_event.is_set():
            self.__clear()
            logger.info(f"Rotator for {self.other_sae.id} has finished")
