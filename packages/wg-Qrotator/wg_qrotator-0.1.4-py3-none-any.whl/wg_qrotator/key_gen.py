import base64
from wolfcrypt.ciphers import MlDsaType, MlDsaPrivate


def gen_id(priv_filename: str, pub_filename: str):
    """Generate ML-DSA-87 key pair encoded as base64 and output it to two files.

    Args:
        priv_filename (str): Path to the file where the private key will be stored.
        pub_filename (str): Path to the file where the public key will be stored.
    """
    alg_type = MlDsaType.ML_DSA_87

    dsa_priv = MlDsaPrivate.make_key(alg_type)
    b64priv_key = base64.b64encode(dsa_priv.encode_priv_key())

    with open(priv_filename, "w") as f:
        f.write(b64priv_key.decode())

    b64pub_key = base64.b64encode(dsa_priv.encode_pub_key())

    with open(pub_filename, "w") as f:
        f.write(b64pub_key.decode())
