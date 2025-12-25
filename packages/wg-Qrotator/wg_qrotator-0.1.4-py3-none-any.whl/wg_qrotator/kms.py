import requests
import ctypes
import base64
import logging
import os
from ctypes import c_char, c_char_p, c_int

from wg_qrotator.peer import SAE
from wg_qrotator.kms_so.libclient_api_structs import *

logger = logging.getLogger(__name__)


class ETSI_014:
    def __init__(self, kms_uri: str, root_crt: str, my_sae: SAE, other_sae: SAE):
        self.kms_uri = kms_uri
        self.root_crt = root_crt
        self.my_sae = my_sae
        self.other_sae = other_sae

    def get_key(self, key_id=None) -> tuple:
        """GET_KEY request.

        Args:
            key_id (_type_, optional): Key id to retrieve. Defaults to None.

        Raises:
            ValueError: Error retrieving key.

        Returns:
            tuple: (key content, key id)
        """
        ROOT_CRT = self.root_crt
        MY_KEY = self.my_sae.key
        MY_CRT = self.my_sae.cert
        KMS_ADDR = self.kms_uri

        if not key_id:
            url = f"{KMS_ADDR}/{self.other_sae.sae_id}/enc_keys?number=1&size=256"
        else:
            url = f"{KMS_ADDR}/{self.other_sae.sae_id}/dec_keys?key_ID={key_id}"

        try:
            response = requests.get(url, cert=(MY_CRT, MY_KEY), verify=ROOT_CRT)
            response.raise_for_status()
            json_response = response.json()

            if "keys" in json_response:
                key = json_response["keys"][0]["key"]
                if not key_id:
                    key_id = json_response["keys"][0]["key_ID"]
                return key, key_id
            else:
                raise ValueError("No 'keys' key found in the response.")

        except requests.RequestException as e:
            logger.error(f"Error occurred during KMS HTTP request: {e}")
        except (KeyError, ValueError) as e:
            logger.error(f"Error occurred while parsing KMS JSON response: {e}")

        return None, None


class ETSI_004:
    def __init__(
        self, kms_uri: str, root_crt: str, my_sae, other_sae, inverted=False, ksid=None
    ) -> None:
        self._api_so = os.path.join(
            os.path.dirname(__file__), "kms_so", "libclient_api.so"
        )
        self.kms_uri = kms_uri
        self.kms_ip = kms_uri.split(":")[0]
        self.kms_port = int(kms_uri.split(":")[1])
        self.root_crt = root_crt
        self.my_sae = my_sae
        self.other_sae = other_sae
        self.client_api = None
        self.ksid = ksid
        self.key_index = None
        self.inverted = inverted
        self._load_so()
        self._open_connect()

    def _load_so(self):
        """Load the shared object containing the interface for ETSI GS QKD 004
        """
        self.client_api = ctypes.CDLL(self._api_so)
        # Define argument types and return types for the functions
        self.client_api.openConnect.argtypes = [
            c_char_p,
            c_char_p,
            c_char_p,
            c_int,
            c_char_p,
            c_char_p,
            c_char_p,
            c_int,
        ]
        self.client_api.openConnect.restype = c_char_p

        self.client_api.getKey.argtypes = [
            c_char_p,
            c_char_p,
            c_char_p,
            c_int,
            c_char,
            c_int,
            c_char_p,
        ]
        self.client_api.getKey.restype = QKD_Get_Key_Response

        self.client_api.close.argtypes = [c_char_p, c_char_p, c_char_p, c_int, c_char_p]
        self.client_api.close.restype = QKD_Close_Response

    def _open_connect(self):
        """OPEN_CONNECT request.

        Raises:
            ValueError: Error opening key session.
        """
        if not self.inverted:
            response = self.client_api.openConnect(
                bytes(self.my_sae.cert, "utf-8"),
                bytes(self.my_sae.key, "utf-8"),
                bytes(self.kms_ip, "utf-8"),
                self.kms_port,
                bytes(self.my_sae.sae_id, "utf-8"),
                bytes(self.other_sae.sae_id, "utf-8"),
                self.ksid,
                32,
            )
        else:
            response = self.client_api.openConnect(
                bytes(self.my_sae.cert, "utf-8"),
                bytes(self.my_sae.key, "utf-8"),
                bytes(self.kms_ip, "utf-8"),
                self.kms_port,
                bytes(self.other_sae.sae_id, "utf-8"),
                bytes(self.my_sae.sae_id, "utf-8"),
                self.ksid,
                32,
            )

        if response is not None:
            self.ksid = response
        else:
            raise ValueError("Failed to open connection")

    def get_key(self, index: int = None) -> tuple:
        """GET_KEY request.

        Args:
            index (int, optional): Key index. Defaults to None.

        Raises:
            ValueError: Error retrieving key.

        Returns:
            tuple: (key content, key index)
        """
        if index is not None:
            self.key_index = index
        elif self.key_index is None:
            self.key_index = 0

        response = self.client_api.getKey(
            bytes(self.my_sae.cert, "utf-8"),
            bytes(self.my_sae.key, "utf-8"),
            bytes(self.kms_ip, "utf-8"),
            self.kms_port,
            c_char(0),
            self.key_index,
            self.ksid,
        )

        if response.status == 0:
            self.key_index += 1
            # Extract the key data
            key_data = base64.b64encode(
                ctypes.string_at(response.key_buffer.data, response.key_buffer.size)
            ).decode("utf-8")
            return key_data, self.key_index - 1
        else:
            raise ValueError(
                "Failed to get key with status code: {}".format(response.status)
            )

    def close(self) -> int:
        """CLOSE request.

        Raises:
            ValueError: Error closing session.

        Returns:
            int: response status
        """
        response = self.client_api.close(
            bytes(self.my_sae.cert, "utf-8"),
            bytes(self.my_sae.key, "utf-8"),
            bytes(self.kms_ip, "utf-8"),
            self.kms_port,
            self.ksid,
        )

        if response.status != 0:
            raise ValueError(
                "Failed to close connection with status code: {}".format(
                    response.status
                )
            )

        return response.status
