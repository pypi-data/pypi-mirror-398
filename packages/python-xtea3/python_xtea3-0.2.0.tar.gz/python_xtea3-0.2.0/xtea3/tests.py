import unittest

from xtea3 import encipher, decipher


class Test(unittest.TestCase):
    def test_network_endian(self):
        origin_data = b'Hello XTEA3 !' * 42
        key_bytes = b'1234567890123456' * 2  # 32 bytes (256 bits)
        num_rounds = 32
        endian = '!'
        encrypted_data = encipher(origin_data, key_bytes, num_rounds, endian)
        decrypted_data = decipher(encrypted_data, key_bytes, num_rounds, endian)
        self.assertTrue(origin_data == decrypted_data)

    def test_little_endian(self):
        origin_data = b'Hello XTEA3 !' * 42
        key_bytes = b'1234567890123456' * 2  # 32 bytes (256 bits)
        num_rounds = 32
        endian = '<'
        encrypted_data = encipher(origin_data, key_bytes, num_rounds, endian)
        decrypted_data = decipher(encrypted_data, key_bytes, num_rounds, endian)
        self.assertTrue(origin_data == decrypted_data)

    def test_big_endian(self):
        origin_data = b'Hello XTEA3 !' * 42
        key_bytes = b'1234567890123456' * 2  # 32 bytes (256 bits)
        num_rounds = 32
        endian = '>'
        encrypted_data = encipher(origin_data, key_bytes, num_rounds, endian)
        decrypted_data = decipher(encrypted_data, key_bytes, num_rounds, endian)
        self.assertTrue(origin_data == decrypted_data)


if __name__ == '__main__':
    unittest.main()
