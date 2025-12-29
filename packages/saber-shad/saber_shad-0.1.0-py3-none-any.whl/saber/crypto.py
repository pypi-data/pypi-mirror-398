import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class Saber:
    _IV = b"\x00" * 16

    @staticmethod
    def _validate_key_len(key: bytes):
        if len(key) not in (16, 24, 32):
            raise ValueError("Invalid AES key length")

    @staticmethod
    def generate_key_from_raw(raw: str) -> bytes:
        if len(raw) < 32: raw = raw.ljust(32, "0")
        p1,p2,p3,p4 = raw[0:8],raw[8:16],raw[16:24],raw[24:32]
        reordered = p3+p1+p4+p2
        out=[]
        for ch in reordered:
            if "0"<=ch<="9": out.append(chr(((ord(ch)-ord("0")+5)%10)+ord("0")))
            elif "a"<=ch<="z": out.append(chr(((ord(ch)-ord("a")+9)%26)+ord("a")))
            else: out.append(ch)
        return "".join(out).encode()

    @staticmethod
    def encrypt_with_raw_key(plain: str, raw: str) -> str|None:
        try:
            key=Saber.generate_key_from_raw(raw);Saber._validate_key_len(key)
            ct=AES.new(key,AES.MODE_CBC,iv=Saber._IV).encrypt(pad(plain.encode(),AES.block_size))
            return base64.b64encode(ct).decode()
        except Exception:
            return None

    @staticmethod
    def decrypt_with_raw_key(enc_b64: str, raw: str) -> str|None:
        try:
            key=Saber.generate_key_from_raw(raw);Saber._validate_key_len(key)
            ct=base64.b64decode(enc_b64)
            pt=unpad(AES.new(key,AES.MODE_CBC,iv=Saber._IV).decrypt(ct),AES.block_size)
            return pt.decode()
        except Exception:
            return None