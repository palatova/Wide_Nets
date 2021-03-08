import socket
import math

def main():
    tmp = length + K
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 9099))
        s.listen()
        conn, addr = s.accept()
        with conn:
            while True:
                n = conn.recv(8)
                n = bytes_Int(n)
                total_err_count = 0
                total_correct_words = 0
                msg_size = math.ceil(
                    tmp / 8)

                for _ in range(n):
                    word = conn.recv(msg_size)
                    word = bytearray(word)
                    _, err_c = Decode(word)
                    total_err_count += err_c
                    if err_c  < 2:
                        total_correct_words += 1

                conn.sendall(int_Bytes(total_err_count))
                conn.sendall(int_Bytes(total_correct_words))

def RecordB(dst : bytearray, src : bytearray, dstart, sstart, count):
    dst_pos = dstart
    src_pos = sstart

    for _ in range(count):
        dst_byte_pos = dst_pos // 8
        dst_bit_pos = dst_pos % 8
        src_byte_pos = src_pos // 8
        src_bit_pos = src_pos % 8
        
        dst_mask = 128 >> dst_bit_pos
        src_mask = 128 >> src_bit_pos
        
        v = src_mask & src[src_byte_pos]
        v = v << src_bit_pos
        v = v >> dst_bit_pos
        dst[dst_byte_pos] = (~dst_mask & dst[dst_byte_pos]) | v
        
        dst_pos += 1
        src_pos += 1
    


def meaningsCb(barr : bytearray, k, msg_len):
    control_bits = []
    for control_bit in range(k):
        n = 2**control_bit
        t = 0
        for i in range(n-1, msg_len, 2*n):
            upper_bound = min(i+n, msg_len)
            for j in range(i, upper_bound):
                byte_index = j // 8
                bit_index = j % 8
                mask = 128 >> bit_index

                if mask & barr[byte_index] > 0:
                    t = t ^ 1

        control_bits.append(t)
    
    return control_bits




def CalculatePB(word, msg_len):
    t = 0
    for i in range(msg_len):
        byte_index = i // 8
        bit_index = i % 8
        mask = 128 >> bit_index
        bit = 0
        if (word[byte_index] & mask) > 0:
            bit = 1
        t = t ^ bit
    
    return t



def GParityBit(word, msg_len):
    byte_pos = msg_len // 8
    bit_pos = msg_len % 8
    
    bit = 0
    mask = 128 >> bit_pos
    if word[byte_pos] & mask > 0:
        bit = 1

    return bit


def bitsByte(bits):
    if len(bits) >= 8:
        raise ValueError('Exception')
    res = 0
    c = 1
    for b in bits:
        if b:
            res += c
        c << 1

    return res

length = 67
K = 7
def RecoverData(msg):
    byte_count = math.ceil(length / 8)
    res = bytearray(byte_count)
    res_bits_count = 0
    total_msg_len = length + K
    block_start = 2
    while block_start < total_msg_len:
        block_end = min(total_msg_len, block_start*2 - 1)
        count = block_end - block_start
        RecordB(res, msg, res_bits_count, block_start, count)
        res_bits_count += count
        block_start *= 2

    return res


def Decode(word):
    msg_len = length + K
    bits = meaningsCb(word, K, length)
    p_extr = GParityBit(word, msg_len)
    p_calc = CalculatePB(word, length + K)
    p = p_calc^p_extr
    c = bitsByte(bits)

    if c == 0:
        return RecoverData(word), 0
    elif c != 0 and p == 1:
        c -= 1
        byte_pos = c // 8
        bit_pos = c % 8

        v = word[byte_pos]
        mask = 128 >> bit_pos
        bit = 1
        if v & mask > 0:
            bit = 0

        word[byte_pos] = (~mask & v) | (bit << (7-bit_pos))
        return RecoverData(word), 1

    return word, 2

def int_Bytes(val):
    return val.to_bytes(8, byteorder='big')


def bytes_Int(bytes):
    return int.from_bytes(bytes, byteorder='big', signed=True)
                

main()
