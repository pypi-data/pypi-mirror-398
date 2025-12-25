import json, socket, select, threading, time, hmac, hashlib, logging, base64
from collections import defaultdict, deque
from wolfcrypt.ciphers import MlDsaType, MlDsaPrivate, MlDsaPublic

import wg_qrotator.exceptions as e
from wg_qrotator import constants

logger = logging.getLogger(__name__)


class SAE:
    def __init__(
        self, id: str, ip: str, port: int, sae_id: str, cert: str, key: str
    ) -> None:
        self.id = id
        self.ip = ip
        self.port = port
        self.sae_id = sae_id
        self.cert = cert
        self.key = key


class Communicator:
    def __init__(
        self, my_ip: str, my_port: int, my_auth_priv_key_filename: str
    ) -> None:
        self.my_ip = my_ip
        self.my_port = my_port
        self.my_auth_priv_key_filename = my_auth_priv_key_filename
        self._msg_id = 0
        self._message_queues = defaultdict(
            lambda: deque(maxlen=constants.MAX_MESSAGE_QUEUE_SIZE)
        )
        self._ping_responses = {}
        self._running = threading.Event()
        self._id_lock = threading.Lock()
        self._ping_lock = threading.Lock()
        self._peer_cookies = {}
        self._peer_back_cookies = {}
        self._peer_hello_cookies = {}
        self._peer_auth_keys = {}
        self._use_dsa = {}
        self._seen_nonces = defaultdict(lambda: deque(maxlen=10000))

    @staticmethod
    def is_acked(msg: dict, msg_id: int) -> bool:
        """Check if message contains the acknowledge to a given message ID

        Args:
            msg (dict): Message content.
            msg_id (int): Message ID to check if `msg` is acknowledging.

        Returns:
            bool: True if `msg` acknowledges `msg_id`, else False.
        """
        ack = msg.get("acked")
        if msg and ack and ack == msg_id:
            return True
        return False

    @staticmethod
    def is_abort(msg: dict) -> bool:
        """Check if a given message is an abort.

        Args:
            msg (dict): message.

        Returns:
            bool: True is message is an abort, else False.
        """
        msg_type = msg.get("msg_type")
        if not msg_type or msg_type == "Abort round":
            return True
        return False

    def dsa_sign(self, data: str) -> str:
        """Sign given data using ML-DSA-87.

        Args:
            data (str): Data to sign.

        Returns:
            str: Signature.
        """
        dsa_type = MlDsaType.ML_DSA_87
        dsa_priv = MlDsaPrivate(dsa_type)
        with open(self.my_auth_priv_key_filename, "r") as f:
            b64_priv_key = f.read()
        priv_bytes = base64.b64decode(b64_priv_key)
        dsa_priv.decode_key(priv_bytes)
        return base64.b64encode(dsa_priv.sign(data)).decode()

    def dsa_verify(self, peer_ip: str, data: str, signature: str) -> bool:
        """Verify ML-DSA-87 signature.

        Args:
            peer_ip (str): IP address of the signer.
            data (str): Data that was signed.
            signature (str): Signature.

        Returns:
            bool: True if the signature is valid, else False.
        """
        dsa_type = MlDsaType.ML_DSA_87
        dsa_pub = MlDsaPublic(dsa_type)
        with open(self._peer_auth_keys[peer_ip], "r") as f:
            b64_priv_key = f.read()
        priv_bytes = base64.b64decode(b64_priv_key)
        dsa_pub.decode_key(priv_bytes)
        signature = base64.b64decode(signature)
        return dsa_pub.verify(signature, data)

    def _generate_nonce(
        self, peer_ip: str, data: dict, timestamp: float = None, source: str = None
    ) -> str:
        """Generate authenticated NONCE (i.e. MAC).

        Args:
            peer_ip (str): IP address of the message receiver.
            data (dict): Message data.
            timestamp (float, optional): Timestamp to include in the message. Defaults to None.
            source (str, optional): Optional source of authentication shared key. Accepts "back" or "hello". Defaults to None.

        Raises:
            ValueError: _description_

        Returns:
            str: _description_
        """
        if timestamp is None:
            data["timestamp"] = time.time()
        data_encoded = f"{data}".encode("utf-8")
        if self._use_dsa.get(peer_ip, False):
            return self.dsa_sign(data_encoded), data
        else:
            if peer_ip not in self._peer_cookies:
                raise ValueError("No shared key for peer")

            key = self._peer_cookies[peer_ip]
            if source == "back":
                key = self._peer_back_cookies[peer_ip]
            elif source == "hello":
                key = self._peer_hello_cookies[peer_ip]

            return hmac.new(key, data_encoded, hashlib.sha256).hexdigest(), data

    def _verify_nonce(
        self, peer_ip: str, data: dict, received_nonce: str, is_hello: bool = False
    ) -> bool:
        """Verify authenticated NONCE (i.e. MAC).

        Args:
            peer_ip (str): IP address of the message sender.
            data (dict): Message data.
            received_nonce (str): Authenticated NONCE value.
            is_hello (bool, optional): True is message is of type "hello". Defaults to False.

        Returns:
            bool: _description_
        """
        nonce_check = False
        if self._use_dsa.get(peer_ip, False):
            encoded_data = f"{data}".encode("utf-8")
            nonce_check = self.dsa_verify(peer_ip, encoded_data, received_nonce)
        else:
            if peer_ip not in self._peer_cookies:
                return False
            expected_nonce, _ = self._generate_nonce(
                peer_ip, data, 1234.0
            )  # 1234 timestamp value just for it to be ignored by _generate_nonce
            if hmac.compare_digest(expected_nonce, received_nonce):
                nonce_check = True

            if not nonce_check and peer_ip in self._peer_back_cookies:
                expected_nonce_back, _ = self._generate_nonce(
                    peer_ip, data, 1234.0, source="back"
                )
                if hmac.compare_digest(expected_nonce_back, received_nonce):
                    nonce_check = True

            if not nonce_check and is_hello and peer_ip in self._peer_hello_cookies:
                expected_nonce_hello, _ = self._generate_nonce(
                    peer_ip, data, 1234.0, source="hello"
                )
                if hmac.compare_digest(expected_nonce_hello, received_nonce):
                    nonce_check = True

        if not nonce_check:
            return False

        if abs(time.time() - data.get("timestamp")) > constants.NONCE_EXPIRY:
            return False

        if received_nonce in self._seen_nonces[peer_ip]:
            return False
        self._seen_nonces[peer_ip].append(received_nonce)
        return True

    def _receive_messages(self) -> None:
        """Receive messages from the peers."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.my_ip, self.my_port))
            sock.listen(5)
            while self._running.is_set():
                # small timeout so we remain responsive to stop_listening()
                readable, _, _ = select.select([sock], [], [], 0.1)
                for readable_socket in readable:
                    client_socket, addr = readable_socket.accept()
                    with client_socket:
                        # Read the 4-byte message length first
                        header = client_socket.recv(4)
                        if not header:
                            continue

                        message_length = int.from_bytes(header, "big")

                        if (
                            message_length <= 0
                            or message_length > constants.MAX_MESSAGE_SIZE
                        ):
                            continue

                        # Read the full message based on length
                        data = b""
                        while len(data) < message_length:
                            packet = client_socket.recv(1024)
                            if not packet:
                                break
                            data += packet

                        if len(data) != message_length:
                            continue

                        # parse JSON once
                        try:
                            msg = json.loads(data.decode("utf-8"))
                        except Exception:
                            continue

                        self._process_incoming_message(msg, addr)

    def _process_incoming_message(self, msg: dict, addr) -> None:
        """Validate incoming messages and saved them if valid.

        Args:
            msg (dict): Message.
            addr (_type_): Address and port of the sender.

        Returns:
            _type_: _description_
        """
        msg_type = msg.get("msg_type")
        peer_ip = addr[0]
        if self._use_dsa.get(peer_ip, False) or peer_ip in self._peer_cookies:
            nonce = msg.pop("nonce")
            if not nonce or not self._verify_nonce(
                peer_ip, msg, nonce, is_hello=msg_type == "Hello"
            ):
                logger.info(f"Message from {addr} dropped due to invalid NONCE")
                return  # drop invalid or replayed message
        else:
            logger.info(f"No authentication data for {addr}")
            return  # drop invalid or replayed message

        # Automatic ping reply: send pong back to sender's listening port.
        if msg_type == "Ping":
            # prefer src_port advertised by sender; fall back to TCP source port
            dst_port = msg.get("src_port", addr[1])
            try:
                pong = {"msg_type": "Pong", "msg_id": msg.get("msg_id")}
                # best-effort: use same raw sender->recipient socket path (separate connection)
                self._send_raw_message(pong, addr[0], dst_port)
            except Exception:
                pass
            return

        # If it's a Pong, signal the waiting event for that ping
        if msg_type == "Pong":
            with self._ping_lock:
                event = self._ping_responses.pop(msg.get("msg_id"), None)
            if event:
                event.set()
            return

        self._message_queues[addr[0]].append(json.dumps(msg))

    def _send_raw_message(self, message: dict, dst_ip: str, dst_port: int) -> None:
        """Simplified message send.

        Args:
            message (dict): Message content.
            dst_ip (str): Destination IP address.
            dst_port (int): Destination port number.

        Raises:
            e.No_cookie_set_for_peer_exception: raised if there's no keys to authenticate the message.
        """
        if self._use_dsa.get(dst_ip, False) or dst_ip in self._peer_cookies:
            if "msg_id" not in message:
                msg_id = self._get_next_msg_id()
                message["msg_id"] = msg_id
            nonce, message = self._generate_nonce(dst_ip, message)
            message["nonce"] = nonce
        else:
            raise e.No_cookie_set_for_peer_exception(
                f"Cannot authenticate message to {dst_ip}"
            )

        data = json.dumps(message).encode("utf-8")
        header = len(data).to_bytes(4, "big")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1.0)
                sock.connect((dst_ip, dst_port))
                sock.sendall(header + data)
        except Exception:
            pass

    def _get_next_msg_id(self) -> int:
        """Calculate the identifier of the next message to be sent.

        Returns:
            int: Message identifier.
        """
        with self._id_lock:
            self._msg_id = (self._msg_id + 1) % 65535  # from 0 to 2**16-1
            return self._msg_id

    def set_peer_cookie(self, peer_ip: str, cookie: bytes) -> None:
        """Set authentication cookie for a peer with a given IP address.

        Args:
            peer_ip (str): Peer IP address.
            cookie (bytes): Cookie (i.e. 32-byte shared key).
        """
        self._peer_cookies[peer_ip] = cookie

    def set_peer_back_cookie(self, peer_ip: str, cookie: bytes) -> None:
        """Set backup authentication cookie for a peer with a given IP address.

        Args:
            peer_ip (str): Peer IP address.
            cookie (bytes): Cookie (i.e. 32-byte shared key).
        """
        self._peer_back_cookies[peer_ip] = cookie

    def set_peer_hello_cookie(self, peer_ip: str, cookie: bytes) -> None:
        """Set authentication cookie for "hello" messages for peer with a given IP address.

        Args:
            peer_ip (str): Peer IP address.
            cookie (bytes): Cookie (i.e. 32-byte shared key).
        """
        self._peer_hello_cookies[peer_ip] = cookie

    def set_peer_auth_key(self, peer_ip: str, key_filename: str) -> None:
        """Set ML-DSA-87 authentication keys for a peer with a given IP address.

        Args:
            peer_ip (str): Peer IP address.
            key_filename (str): Path of the file containing the peer's ML-DSA public key.
        """
        self._peer_auth_keys[peer_ip] = key_filename

    def set_use_dsa(self, peer_ip: str, use: bool) -> None:
        """Turn on or off the usage of ML-DSA for message authentication.

        Args:
            peer_ip (str): Peer IP address.
            use (bool): Usage flag.
        """
        self._use_dsa[peer_ip] = use

    def get_peer_cookie(self, peer_ip: str) -> bytes:
        """Get peer authentication cookie.

        Args:
            peer_ip (str): Peer IP address.

        Returns:
            bytes: Cookie content.
        """
        return self._peer_back_cookies.get(peer_ip)

    def wait_for_ack(
        self, period: float, max_tries: int, msg_id: int, other_sae_ip: str
    ) -> None:
        """Wait for acknowledge message.

        Args:
            period (float): Time period (in seconds) between consecutive message receiving tries.
            max_tries (int): Message receiving maximum tries.
            msg_id (int): Message identifier that is to be acknowledged.
            other_sae_ip (str): Peer IP address to receive the message from.

        Raises:
            e.Connection_timeout: Acknowledge message receiving timeout.
        """
        rcv_msg = self.wait_for_message(
            period, max_tries, other_sae_ip, message_types=["Ack"]
        )
        if not Communicator.is_acked(rcv_msg, msg_id):
            raise e.Connection_timeout(period * max_tries)

    def send_message(
        self,
        message: dict,
        dst_ip: str,
        dst_port: int,
        wait_for_ack: bool = False,
        timeout: int = 5,
    ) -> int:
        """Send message.

        Args:
            message (dict): Message content.
            dst_ip (str): Destination IP address.
            dst_port (int): Destination port number.
            wait_for_ack (bool, optional): Send message and wait for its acknowledgement. Defaults to False.
            timeout (int, optional): Message send timeout. Defaults to 5.

        Raises:
            e.No_cookie_set_for_peer_exception: Raised if there's no keys to authenticate the message.
            e.Connection_timeout: Raised if message send (and acknowledgement wait) has timeout.

        Returns:
            int: Message identifier of the sent message.
        """
        if self._use_dsa.get(dst_ip, False) or dst_ip in self._peer_cookies:
            msg_id = self._get_next_msg_id()
            message["msg_id"] = msg_id
            nonce, message = self._generate_nonce(dst_ip, message)
            message["nonce"] = nonce
        else:
            raise e.No_cookie_set_for_peer_exception(
                f"Cannot authenticate message to {dst_ip}"
            )

        message = json.dumps(message).encode("utf-8")

        # Add length prefix (4-byte big-endian)
        message_length = len(message)
        header = message_length.to_bytes(4, "big")  # 4-byte header

        start_time = time.time()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            while time.time() - start_time < timeout:
                try:
                    sock.connect((dst_ip, dst_port))
                    sock.sendall(header + message)  # Send header and message
                    if wait_for_ack:
                        self.wait_for_ack(0.0001, 100000, msg_id, dst_ip)
                    return msg_id
                except Exception:
                    time.sleep(0.5)  # Retry after delay
            raise e.Connection_timeout(timeout)

    def wait_for_message(
        self, period: float, max_tries: int, other_sae_ip: str, message_types: list = []
    ) -> dict:
        """Wait for a message from peer.

        Args:
            period (float): Time period (in seconds) between consecutive message receiving checks.
            max_tries (int): Maximum tries to receive the message.
            other_sae_ip (str): Peer IP address.
            message_types (list, optional): List of message types to accept. Defaults to [].

        Raises:
            e.Connection_timeout: Raised if the message waiting has timed out.

        Returns:
            dict: Received message content.
        """
        tries = 0
        while max_tries == -1 or tries < max_tries:
            time.sleep(period)
            tries += 1
            if self.has_messages_from(other_sae_ip):
                try:
                    msg = json.loads(self.get_message_from(other_sae_ip))
                except json.JSONDecodeError:
                    continue
                if msg.get("msg_type") not in message_types:
                    continue
                if Communicator.is_abort(msg):
                    e.Rotation_exception("Rotation round aborted")
                return msg
        raise e.Connection_timeout(period * max_tries)

    def start_listening(self) -> None:
        """Start listening for messages."""
        self._running.set()
        threading.Thread(target=self._receive_messages, daemon=True).start()

    def stop_listening(self) -> None:
        """Stop listening for messages."""
        self._running.clear()

    def has_messages_from(self, ip: str) -> bool:
        """Check if there's a received message from a given IP address.

        Args:
            ip (str): IP address of the sender.

        Returns:
            bool: True if there's at least one message, else False.
        """
        return bool(self._message_queues[ip])

    def get_message_from(self, ip: str) -> dict:
        """Get the oldest message received from a given IP address.

        Args:
            ip (str): IP address of the sender.

        Returns:
            dict: Message content.
        """
        return self._message_queues[ip].popleft() if self._message_queues[ip] else None

    def send_ping(self, dst_ip: str, dst_port: int, timeout: float = 2.0) -> bool:
        """Send a ping message to a given peer.

        Args:
            dst_ip (str): Destination IP address.
            dst_port (int): Destination port number.
            timeout (float, optional): Maximum time (in seconds) for trying to send the message. Defaults to 2.0.

        Returns:
            bool: _description_
        """
        msg_id = self._get_next_msg_id()
        ping = {"msg_type": "Ping", "msg_id": msg_id, "src_port": self.my_port}

        event = threading.Event()
        with self._ping_lock:
            self._ping_responses[msg_id] = event

        # Fire-and-forget send; the reply will come back as a separate inbound connection
        self._send_raw_message(ping, dst_ip, dst_port)

        return event.wait(timeout)
