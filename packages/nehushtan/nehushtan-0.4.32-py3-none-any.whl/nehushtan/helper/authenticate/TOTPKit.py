import base64
import hashlib
import random
import time
from typing import Tuple


class TOTPKit:
    def __init__(
            self,
            shared_secret: bytes,
            otp_length: int = 6,
            otp_seconds: int = 30
    ):
        self.__hash_algo = "sha1"
        self.__B = 64
        # every 30 seconds
        self.__F = otp_seconds
        self.__shared_secret = shared_secret  # b'BASE32SECRET2345AB=='
        # OTP Length
        self.__Digits = otp_length
        self.__key = self.__generate_key()

    @staticmethod
    def generate_shared_secret_with_base32() -> bytes:
        """
        Generate 20 bytes with Base32 supported.

        The most widely used Base32 alphabet is defined in RFC 4648.
        It uses an alphabet of A–Z, followed by 2–7.
        The digits 0, 1 and 8 are skipped due to their similarity with the letters O, I and B
        (thus "2" has a decimal value of 26).
        """

        shared_secret = []
        d = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
        # d = 'abcdefghijklmnopqrstuvwxyz234567'
        for i in range(20):
            b = d[random.Random().randint(0, len(d) - 1)]
            shared_secret.append(b.encode())
        return b''.join(shared_secret)

    @staticmethod
    def generate_key_with_base_32(shared_secret: bytes) -> bytes:
        """
        Google Authenticator Compatility (BASE-32)
        """
        return base64.b32decode(shared_secret + b'=' * (8 - len(shared_secret) % 8))

    def __generate_key(self) -> bytes:
        return TOTPKit.generate_key_with_base_32(self.__shared_secret)

    def __my_hmac(self, key: bytes, message: bytes) -> bytes:
        trans_5c = bytes((x ^ 0x5C) for x in range(256))
        trans_36 = bytes((x ^ 0x36) for x in range(256))
        k_zpad = key.ljust(self.__B, b'\0')
        k_ipad = k_zpad.translate(trans_36)
        k_opad = k_zpad.translate(trans_5c)
        hash1 = hashlib.new(self.__hash_algo, k_ipad + message).digest()
        hmac_hash = hashlib.new(self.__hash_algo, k_opad + hash1).digest()
        return hmac_hash

    def __dynamic_truncate(self, b_hash) -> int:
        hash_len = len(b_hash)
        int_hash = int.from_bytes(b_hash, byteorder='big')
        offset = int_hash & 0xF
        # Geterate a mask to get bytes from left to right of the hash
        n_shift = 8 * (hash_len - offset) - 32
        mask = 0xFFFFFFFF << n_shift
        hex_mask = "0x" + ("{:0" + str(2 * hash_len) + "x}").format(mask)
        p = (int_hash & mask) >> n_shift  # Get rid of left zeros
        lsb_31 = p & 0x7FFFFFFF  # Return only the lower 31 bits
        return lsb_31

    def __generate_TOTP_tuple(self, apply_time: int) -> Tuple[int, int, int, str]:
        """
        With an apply time, generate TOTP for it.

        Return a tuple with:
            apply_time
            available_time
            expire_time
            TOTP
        """
        # %30 seconds
        formated_time = int(apply_time / self.__F)
        t = formated_time.to_bytes(8, byteorder='big')
        # Same algorithm as HOTP
        hmac_hash = self.__my_hmac(self.__key, t)
        trc_hash = self.__dynamic_truncate(hmac_hash)  # Get truncated hash (int)
        # Adjust totp length
        totp = ("{:0" + str(self.__Digits) + "}").format(trc_hash % (10 ** self.__Digits))
        return apply_time, formated_time * self.__F, formated_time * self.__F + self.__F, totp

    def generate_current_TOTP_tuple(self) -> Tuple[int, int, int, str]:
        """
        Generate TOTP for current time.

        Return a tuple with:
            apply_time
            available_time
            expire_time
            TOTP
        """
        t0 = int(time.time())
        totp_now = self.__generate_TOTP_tuple(t0)
        return totp_now
