codes = {
    # ----- NOP -----
    '.': "000",

    # ----- Manipulation (001 mnip) -----
    '>': "001000",   # increment
    '<': "001001",   # decrement
    '_': "001010",   # clear to 0
    '~': "001011",   # clear to init

    # ----- Page Select (010 int2) -----
    '@': "010000",   # page 0
    'A': "010001",   # page 1
    'B': "010010",   # page 2
    'C': "010011",   # page 3
    'X': "010100",
    'Y': "010101",
    'Z': "010110",
    '&': "010111",

    # ----- Arithmetic (011 armd) -----
    '+': "011000",  # add
    '-': "011001",  # sub
    '*': "011010",  # mul
    '/': "011011",  # div
    '=': "011100",  # set A = B
    '#': "011101",  # set A = byte (no B)
    '^': "011110",  # exponent
    'v': "011111",  # root

    # ----- Display (100 addr dpmd) -----
    '|': "10000",  # display binary
    '%': "10001",  # display decimal
    'h': "10010",  # display hex
    'u': "10011",  # display utf8

    # ----- Block instructions (101 blok) -----
    '?': "101000",  # IF
    'R': "101001",  # REPEAT
    'F': "101010",  # FUNCTION DEF
    'U': "101011",  # UNDEF
    'S': "101100",  # CALL
    'L': "1011010",  # FOR
    'V': "1011011",
    'W': "101110",  # WHILE
    ' ': "101111",  # NONE

    # ----- Block end -----
    ']': "110",

    # ----- IO (111 iocd) -----
    'x': "11100",   # exit ok
    'E': "11101",   # exit error
    'H': "11110",   # await hex → next nibble = addr
    'D': "11111",   # await decimal → next nibble = addr

    # ----- Nibbles (operands) -----
    '0': "0000",
    '1': "0001",
    '2': "0010",
    '3': "0011",
    '4': "0100",
    '5': "0101",
    '6': "0110",
    '7': "0111",
    '8': "1000",
    '9': "1001",
    'a': "1010",
    'b': "1011",
    'c': "1100",
    'd': "1101",
    'e': "1110",
    'f': "1111",

    # ----- 2-bit numbers -----
    'i':'00',
    'j':'01',
    'k':'10',
    'l':'11'
}

def binaryToBytes(binary:str):
    if("0b" in binary):
        binary = binary[2:]
    binary = "".join([b for b in binary if not b.isspace()])
    while len(binary) % 8 > 0:
        binary+="0"
    byte = int(binary, 2)
    byte = byte.to_bytes((len(binary) // 8), byteorder="big")
    return byte

def convert(bitcode:str, file:str=False):
    bitcode = bitcode.replace("[", "").replace("(", "").replace(")", "")
    
    bits = ""
    skip = False
    for i, ch in enumerate(bitcode):
        if(ch == ";"):
            skip = not skip
            continue
        if(skip):
            continue
        if ch.isspace():
            continue
        if ch in codes:
            bits += codes[ch]
        else:
            print(f"COMPILATION ERROR: Illegal character '{ch}' found at position {i}")
            print(f"Context: ...{bitcode[max(0, i-5):i+5]}...")
            return None
    if(skip):
        print("Unclosed comment: please ensure all comments are closed correctly and try again")
        return None
    if(file):
        file = open(file, "wb")
        file.write(binaryToBytes(bits))
        file.close()
    return bits