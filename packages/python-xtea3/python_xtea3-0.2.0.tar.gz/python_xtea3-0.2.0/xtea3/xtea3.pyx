from struct import pack, unpack


cdef unsigned int rol(unsigned int val, unsigned int shift):
    shift &= 0x1F
    return ((val << shift) | (val >> (32 - shift))) & 0xFFFFFFFF


cdef list encipher_block(list v, list k, int num_rounds):
    cdef unsigned int a = (v[0] + k[0]) & 0xFFFFFFFF
    cdef unsigned int b = (v[1] + k[1]) & 0xFFFFFFFF
    cdef unsigned int c = (v[2] + k[2]) & 0xFFFFFFFF
    cdef unsigned int d = (v[3] + k[3]) & 0xFFFFFFFF
    cdef unsigned int sum_ = 0
    cdef unsigned int delta = 0x9E3779B9
    for i in range(num_rounds):
        a = (a + (((b << 4) + rol(k[(sum_ % 4) + 4], b)) ^ (d + sum_) ^ ((b >> 5) + rol(k[sum_ % 4], b >> 27)))) & 0xFFFFFFFF
        sum_ = (sum_ + delta) & 0xFFFFFFFF
        c = (c + (((d << 4) + rol(k[((sum_ >> 11) % 4) + 4], d)) ^ (b + sum_) ^ ((d >> 5) + rol(k[(sum_ >> 11) % 4], d >> 27)))) & 0xFFFFFFFF
        t = a
        a = b
        b = c
        c = d
        d = t
    return [a ^ k[4], b ^ k[5], c ^ k[6], d ^ k[7]]


cdef list decipher_block(list v, list k, int num_rounds):
    cdef unsigned int delta = 0x9E3779B9
    cdef unsigned int sum_ = (delta * num_rounds) & 0xFFFFFFFF
    cdef unsigned int d = v[3] ^ k[7]
    cdef unsigned int c = v[2] ^ k[6]
    cdef unsigned int b = v[1] ^ k[5]
    cdef unsigned int a = v[0] ^ k[4]
    for i in range(num_rounds):
        t = d
        d = c
        c = b
        b = a
        a = t
        c = (c - (((d << 4) + rol(k[((sum_ >> 11) % 4) + 4], d)) ^ (b + sum_) ^ ((d >> 5) + rol(k[(sum_ >> 11) % 4], d >> 27)))) & 0xFFFFFFFF
        sum_ = (sum_ - delta) & 0xFFFFFFFF
        a = (a - (((b << 4) + rol(k[(sum_ % 4) + 4], b)) ^ (d + sum_) ^ ((b >> 5) + rol(k[sum_ % 4], b >> 27)))) & 0xFFFFFFFF
    return [(a - k[0]) & 0xFFFFFFFF, (b - k[1]) & 0xFFFFFFFF, (c - k[2]) & 0xFFFFFFFF, (d - k[3]) & 0xFFFFFFFF]


cdef bytes pad_bytes(bytes data, int block_size):
    cdef unsigned int padding = (block_size - len(data) % block_size) % block_size
    return data + b'\x00' * padding


cdef list data_to_blocks(bytes data, int block_words, str endian):
    cdef unsigned int word_size = 4
    cdef str unpack_fmt = f'{endian}{block_words}I'
    cdef unsigned int block_size = block_words * word_size
    cdef bytes pad_data = pad_bytes(data, block_size)
    cdef list blocks = []
    for i in range(0, len(pad_data), block_size):
        blocks.append(list(unpack(unpack_fmt, pad_data[i:i + block_size])))
    return blocks


cdef bytes blocks_to_bytes(list blocks, str endian):
    return b''.join([pack(f'{endian}{len(block)}I', *block) for block in blocks])


cpdef bytes encipher(bytes data, bytes key_bytes, int num_rounds, str endian):
    cdef list key = list(unpack(f'{endian}8I', key_bytes))
    cdef list plain_blocks = data_to_blocks(data, 4, endian)
    cdef list encrypted_blocks = [encipher_block(block, key, num_rounds) for block in plain_blocks]
    cdef bytes cipher_data = blocks_to_bytes(encrypted_blocks, endian)
    return cipher_data


cpdef bytes decipher(bytes cipher_data, bytes key_bytes, int num_rounds, str endian):
    cdef list key = list(unpack(f'{endian}8I', key_bytes))
    cdef list enc_blocks = data_to_blocks(cipher_data, 4, endian)
    cdef list decrypted_blocks = [decipher_block(block, key, num_rounds) for block in enc_blocks]
    cdef bytes decrypted_data = blocks_to_bytes(decrypted_blocks, endian)
    return decrypted_data.rstrip(b'\x00')
