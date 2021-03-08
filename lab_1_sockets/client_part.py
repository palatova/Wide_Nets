import random
import socket
import math

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('127.0.0.1' , 9099))

        l = input('Введите название файла, в котором содержится сообщение\n')
        while l != 'stop':
            num = input('Введите количество ошибок на слово\n')
            if num == 'stop':
                break
            mode = int(num)
            with open(l,'rb') as f:
                data = f.read() 
            words = BytesWords(data)
            words = [Encode(word) for word in words]
            correct_gen, err_count_gen = Insrt(words, 0.2, mode)
            n = len(words)
            s.sendall(int_Bytes(n))
            for _, word in enumerate(words):
                s.sendall(word)

            total_err = bytes_Int(s.recv(8))
            correct_words = bytes_Int(s.recv(8))
            print(f'Всего исправленных ошибок :  {total_err}; всего добавленных ошибок : {err_count_gen}')
            print(f'Количество правильно доставленных слов : {correct_words}')
            print(f'Количество неправильно доставленных слов : {n-correct_words}')

def Insrt(words, worng_word_rate, mode):
    correct_words = len(words)
    err_count = 0  
    if mode == 0:
        return correct_words, err_count
    elif mode == 1:
        for i in range(len(words)):
            if random.random() < worng_word_rate:
                index = random.randint(0, WORD_SIZE-1)
                Error_insertion(words[i], index)
                correct_words -= 1
                err_count += 1
    else:
        for i in range(len(words)):
            if random.random() < worng_word_rate:
                index1 = random.randint(0, WORD_SIZE-1)
                index2 = random.randint(0, WORD_SIZE-1)
                if index1 == index2:
                    if index1 > 0:
                        index1 -= 1
                    else:
                        index1 += 1
                Error_insertion(words[i], index1)
                Error_insertion(words[i], index2)
                correct_words -= 1
                err_count += 2

    return correct_words, err_count

    
def first_cb(word, msg_len):
    sstart = 0
    k = 2
    dst = bytearray(math.ceil(msg_len / 8))

    while k < msg_len:
        i = k
        j = min(msg_len, 2*k-1)
        count = j - i
        Meaning_to_bits(dst, word, i, sstart, count)
        sstart += count
        k *= 2

    return dst


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

WORD_SIZE = 67
K = 7
def Insrt_cb_(barr : bytearray, k, control_bits):
    c_bit_pos = 1
    for i in range(k):
        byte_pos = (c_bit_pos-1) // 8
        bit_pos = (c_bit_pos-1) % 8

        v = barr[byte_pos]
        mask = 128 >> bit_pos
        cbit = control_bits[i] << (7 - bit_pos)
        barr[byte_pos] = (v & ~mask) | cbit

        c_bit_pos *= 2


def CParityBit(word, msg_len):
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


def IParityBit(word, msg_len, bit):
    if msg_len == len(word) * 8:
        word = word + bytearray.fromhex('00')
    
    byte_pos = msg_len // 8
    bit_pos = msg_len % 8

    v = word[byte_pos]
    mask = 128 >> bit_pos
    word[byte_pos] = (~mask & v) | (bit << (7 - bit_pos))
    
    return word


def Encode(word):
    word = first_cb(word, WORD_SIZE + K)
    control_bits = meaningsCb(word, K, WORD_SIZE)
    Insrt_cb_(word, K, control_bits)
    msg_len = WORD_SIZE + K
    bit = CParityBit(word, msg_len)
    word = IParityBit(word, msg_len, bit)

    return word


def Meaning_to_bits(dst : bytearray, src : bytearray, dstart, sstart, count):
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
    

def Error_insertion(word, index):
    byte_pos = index // 8
    bit_pos = index % 8
    mask = 128 >> bit_pos
    bit = 1
    if word[byte_pos] & mask > 0:
        bit = 0
    word[byte_pos] = (~mask & word[byte_pos]) | (bit << (7 - bit_pos) )



def BytesWords(data : bytearray):
    words = []
    n = math.ceil(len(data) * 8 / WORD_SIZE)
    word_size_in_bytes = math.ceil(WORD_SIZE / 8)

    data_pos = 0
    for i in range(n):
        word = bytearray(word_size_in_bytes)
        count = min(WORD_SIZE, len(data) - i*WORD_SIZE)
        Meaning_to_bits(word, data, 0, data_pos, count)
        data_pos += WORD_SIZE
        words.append(word)
    
    return words
     
random.seed(1)


def int_Bytes(val):
    return val.to_bytes(8, byteorder='big')


def bytes_Int(bytes):
    return int.from_bytes(bytes, byteorder='big', signed=True)


main()
