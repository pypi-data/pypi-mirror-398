# python-xtea3

[![GitHub Actions](https://github.com/pikhovkin/python-xtea3/actions/workflows/tests.yaml/badge.svg)](https://github.com/pikhovkin/python-xtea3/actions)
[![PyPI - Version](https://img.shields.io/pypi/v/python-xtea3.svg)](https://pypi.org/project/python-xtea3)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/python-xtea3.svg)](https://pypi.org/project/python-xtea3)
[![PyPI - License](https://img.shields.io/pypi/l/python-xtea3.svg)](./LICENSE)

[![Buy me a coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-FFDD00?logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/pikhovkin)
[![Support me](https://img.shields.io/badge/Support%20me-F16061?logo=ko-fi&logoColor=white&labelColor=F16061)](https://ko-fi.com/pikhovkin)
[![Patreon](https://img.shields.io/badge/Patreon-F96854?logo=patreon)](https://patreon.com/pikhovkin)
[![Liberapay](https://img.shields.io/badge/Liberapay-F6C915?logo=liberapay&logoColor=black)](https://liberapay.com/pikhovkin)

XTEA3 implementation

### Installation

```console
pip install python-xtea3
```

### How to use

```python
from xtea3 import encipher, decipher

origin_data = b'Hello XTEA3 !' * 42
key_bytes = b'1234567890123456' * 2  # 32 bytes (256 bits)
num_rounds = 32
endian = '!'

encrypted_data = encipher(origin_data, key_bytes, num_rounds, endian)
print(encrypted_data.hex())

decrypted_data = decipher(encrypted_data, key_bytes, num_rounds, endian)
print(decrypted_data)
assert origin_data == decrypted_data
```

## License

MIT
