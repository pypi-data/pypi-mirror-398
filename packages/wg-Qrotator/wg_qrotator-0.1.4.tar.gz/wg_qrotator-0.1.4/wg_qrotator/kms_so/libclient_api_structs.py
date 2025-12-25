from ctypes import c_char_p, c_uint32, c_void_p, c_uint8, Structure

class QKD_QoS(Structure):
    _fields_ = [
        ("key_chunk_size", c_uint32),
        ("max_bps", c_uint32),
        ("min_bps", c_uint32),
        ("jitter", c_uint32),
        ("priority", c_uint32),
        ("timeout", c_uint32),
        ("ttl", c_uint32),
        ("metadata_mimetype", c_char_p)
    ]

class QKD_Bytes(Structure):
    _fields_ = [
        ("size", c_uint32),
        ("data", c_void_p)
    ]

class UUID_T(Structure):
    _fields_ = [("uuid", c_uint8 * 16)]

class QKD_Open_Connect_Response(Structure):
    _fields_ = [
        ("status", c_uint32),
        ("qos", QKD_QoS),
        ("key_stream_id", UUID_T)
    ]

class QKD_Get_Key_Response(Structure):
    _fields_ = [
        ("status", c_uint32),
        ("index", c_uint32),
        ("key_buffer", QKD_Bytes),
        ("metadata", QKD_Bytes)
    ]

class QKD_Close_Response(Structure):
    _fields_ = [
        ("status", c_uint32)
    ]