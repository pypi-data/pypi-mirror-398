import base64
from wolfcrypt.ciphers import MlKemType, MlKemPrivate, MlKemPublic

from wg_qrotator import constants, exceptions, peer


def get_alg(kem: str) -> MlKemType:
    """Get wolfcrypt cipher type instance from KEM identifier.

    Args:
        kem (str): KEM identifier.

    Raises:
        exceptions.KEM_not_supported_exception: When the provided KEM identifier is not supported.

    Returns:
        MlKemType: Respective wolfcrypt cipher type.
    """
    if kem not in constants.SUPPORTED_KEMS:
        raise exceptions.KEM_not_supported_exception(kem)

    if kem == "ML_KEM_512":
        return MlKemType.ML_KEM_512
    elif kem == "ML_KEM_768":
        return MlKemType.ML_KEM_768
    elif kem == "ML_KEM_1024":
        return MlKemType.ML_KEM_1024
    else:
        raise exceptions.KEM_not_supported_exception(kem)


def handshake(
    key_sources: list, role: str, communicator: peer.Communicator, other_sae: peer.SAE
) -> bytes:
    """One or more two-way PQ key exchanges using KEMs.

    Args:
        key_sources (list): Information about key exchanges to be performed
        role (str): role to be played
        communicator (Communicator): Communicator instance to communicate with peer
        other_sae (SAE): Information about the peer to perform the key exchange with.

    Returns:
        bytes: Generated shared key (XOR of all generated keys).
    """
    combined_key = b"\x00" * 32

    for key_source in key_sources:
        if key_source in constants.SUPPORTED_KEMS:
            kem_type = get_alg(key_source)

            # Generate ephemeral key-pair
            kem_my_priv = MlKemPrivate.make_key(kem_type)

            kem_peer_pub = MlKemPublic(kem_type)

            if role == "client":
                # Send ephemeral public key
                communicator.send_message(
                    {
                        "msg_type": f"{key_source}_ephemeral",
                        "pub_key": base64.b64encode(
                            kem_my_priv.encode_pub_key()
                        ).decode(),
                    },
                    other_sae.ip,
                    other_sae.port,
                )

                # Receive peer's ephemeral public key
                msg = communicator.wait_for_message(
                    constants.LISTEN_TRIES_PERIOD,
                    constants.LISTEN_TIMEOUT_TRIES,
                    other_sae.ip,
                    message_types=[f"{key_source}_ephemeral"],
                )
                kem_peer_pub.decode_key(base64.b64decode(msg.get("pub_key")))

                # Send encapsulated key
                result_0, ct = kem_peer_pub.encapsulate()
                communicator.send_message(
                    {
                        "msg_type": key_source,
                        "kem": base64.b64encode(ct).decode(),
                    },
                    other_sae.ip,
                    other_sae.port,
                )

                # Receive ciphertext and decapsulate
                msg = communicator.wait_for_message(
                    constants.LISTEN_TRIES_PERIOD,
                    constants.LISTEN_TIMEOUT_TRIES,
                    other_sae.ip,
                    message_types=[key_source],
                )
                ct_peer = base64.b64decode(msg.get("kem"))
                result_1 = kem_my_priv.decapsulate(ct_peer)
            else:
                # Receive peer's ephemeral public key
                msg = communicator.wait_for_message(
                    constants.LISTEN_TRIES_PERIOD,
                    constants.LISTEN_TIMEOUT_TRIES,
                    other_sae.ip,
                    message_types=[f"{key_source}_ephemeral"],
                )
                kem_peer_pub.decode_key(base64.b64decode(msg.get("pub_key")))

                # Send ephemeral public key
                communicator.send_message(
                    {
                        "msg_type": f"{key_source}_ephemeral",
                        "pub_key": base64.b64encode(
                            kem_my_priv.encode_pub_key()
                        ).decode(),
                    },
                    other_sae.ip,
                    other_sae.port,
                )

                # Receive ciphertext and decapsulate
                msg = communicator.wait_for_message(
                    constants.LISTEN_TRIES_PERIOD,
                    constants.LISTEN_TIMEOUT_TRIES,
                    other_sae.ip,
                    message_types=[key_source],
                )
                ct_peer = base64.b64decode(msg.get("kem"))
                result_0 = kem_my_priv.decapsulate(ct_peer)

                # Send encapsulated key
                result_1, ct = kem_peer_pub.encapsulate()
                communicator.send_message(
                    {
                        "msg_type": key_source,
                        "kem": base64.b64encode(ct).decode(),
                    },
                    other_sae.ip,
                    other_sae.port,
                )

            # XOR the results into the combined key
            if result_0 and result_1:
                intermediate_key = bytes(x ^ y for x, y in zip(result_0, result_1))
                combined_key = bytes(
                    x ^ y for x, y in zip(combined_key, intermediate_key)
                )

    return combined_key
