# =============================================================
#   VM for custom ISA (variable-length, bitstream-based)
# =============================================================

class BitStream:
    def __init__(self, bits: str):
        self.bits = bits.replace(" ","").replace("\n", "")
        self.pos = 0

    def read(self, n):
        """Read n bits as a string."""
        if self.pos + n > len(self.bits):
            raise RuntimeError("Unexpected end of bitstream")
        out = self.bits[self.pos:self.pos+n]
        self.pos += n
        return out

    def peek(self, n):
        if self.pos + n > len(self.bits):
            raise RuntimeError("Unexpected end of bitstream")
        return self.bits[self.pos:self.pos+n]

    def eof(self):
        return self.pos >= len(self.bits)


# =============================================================
#                     THE VIRTUAL MACHINE
# =============================================================

class VM:
    def __init__(self, bitcode: str):
        if(all(b in "01" for b in bitcode)):
            self.code = BitStream(bitcode)
        else:
            try:
                with open(bitcode, "rb") as file:
                    self.code = BitStream(''.join(format(byte, '08b') for byte in file.read()))
            except:
                raise ValueError("bitcode argument was improperly formatted")
        # 4 pages × 16 addresses × 16-bit values
        self.pages = [[i for i in range(16)] for _ in range(8)]
        self.page = 0  # current page (0–3)

        # function table {id: bitstring}
        self.functions = {}

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    def read_int(self, bs):
        return int(bs, 2)

    def get(self, addr):
        return self.pages[self.page][addr]

    def set(self, addr, value):
        self.pages[self.page][addr] = value & 0xFFFF
        for p in range(8):
            self.pages[p][15] = self.pages[self.page][15]

    # ---------------------------------------------------------
    # Display
    # ---------------------------------------------------------
    def display(self, value, mode):
        if mode == 0:   # utf-8 char
            print(chr(value), end='')
        elif mode == 1:  # decimal
            print(value)
        elif mode == 2:  # hex
            print(hex(value)[2:].upper())
        elif mode == 3:  # utf-8 char (immediate)
            print(chr(value), end="")

    # ---------------------------------------------------------
    # Arithmetic modes
    # ---------------------------------------------------------
    def arithmetic(self, mode, a1, a2, bs):
        v1 = self.get(a1)
        v2 = self.get(a2)

        if mode == 0:   res = v1 + v2
        elif mode == 1: res = v1 - v2
        elif mode == 2: res = v1 * v2
        elif mode == 3: res = 0 if v2 == 0 else v1 // v2
        elif mode == 4: res = v2
        elif mode == 5: res = self.read_int(bs.read(8))
        elif mode == 6: res = (v1 ** v2) if v2 < 16 else 0
        elif mode == 7: res = int(v1 ** (1 / v2)) if v2 != 0 else 0
        else: res = v1

        self.set(a1, res)

    # ---------------------------------------------------------
    # Manipulations
    # ---------------------------------------------------------
    def manipulate(self, mode, addr):
        v = self.get(addr)
        if mode == 0: v = (v + 1) & 0xFF
        elif mode == 1: v = (v - 1) & 0xFF
        elif mode == 2: v = 0
        elif mode == 3: v = addr  # init value = address index
        self.set(addr, v)

    # ---------------------------------------------------------
    # Condition evaluation
    # ---------------------------------------------------------
    def cond(self, mode, a1, a2):
        v1 = self.get(a1)
        v2 = self.get(a2)

        if mode == 0: return v1 == v2
        if mode == 1: return v1 <= v2
        if mode == 2: return v1 >= v2
        if mode == 3: return v1 != v2
        return False

    # ---------------------------------------------------------
    # EXECUTION ENGINE
    # ---------------------------------------------------------
    def run(self, bs=None):
        """Run starting at current code position or from a BitStream."""
        if bs is None:
            bs = self.code

        while not bs.eof():
            op = bs.read(3)

            # -------------------------------------------------
            # 000 NOP
            # -------------------------------------------------
            if op == "000":
                continue

            # -------------------------------------------------
            # 001 %mnip %addr
            # -------------------------------------------------
            elif op == "001":
                mnip = self.read_int(bs.read(3))
                addr = self.read_int(bs.read(4))
                self.manipulate(mnip, addr)

            # -------------------------------------------------
            # 010 %int2 => page switch
            # -------------------------------------------------
            elif op == "010":
                self.page = self.read_int(bs.read(3))

            # -------------------------------------------------
            # 011 %armd %addr %addr
            # -------------------------------------------------
            elif op == "011":
                mode = self.read_int(bs.read(3))
                a1 = self.read_int(bs.read(4))
                if(not mode == 5):
                    a2 = self.read_int(bs.read(4))
                else:
                    a2 = 0
                self.arithmetic(mode, a1, a2, bs)

            # -------------------------------------------------
            # 100 %addr %dpmd
            # -------------------------------------------------
            elif op == "100":
                mode = self.read_int(bs.read(2))
                if(mode < 3):
                    addr = self.read_int(bs.read(4))
                    self.display(self.get(addr), mode)
                else:
                    value = self.read_int(bs.read(8))
                    self.display(value,mode)

            # -------------------------------------------------
            # 101 %blok
            # -------------------------------------------------
            elif op == "101":
                self.handle_block(bs)

            # -------------------------------------------------
            # 110 block terminator
            # -------------------------------------------------
            elif op == "110":
                return  # return to caller inside a block

            # -------------------------------------------------
            # 111 %iocd
            # -------------------------------------------------
            elif op == "111":
                self.handle_iocd(bs)

    # ---------------------------------------------------------
    # Handle I/O codes
    # ---------------------------------------------------------
    def handle_iocd(self, bs):
        code = self.read_int(bs.read(2))

        if code == 0:  # exit no error
            exit(0)

        elif code == 1:  # exit error
            exit(1)

        elif code == 2:  # await hex -> store in addr
            addr = self.read_int(bs.read(4))
            val = int(input("hex> "), 16)
            self.set(addr, val)

        elif code == 3:  # await binary -> store in addr
            addr = self.read_int(bs.read(4))
            val = int(input("dec> "), 10)
            self.set(addr, val)

    # ---------------------------------------------------------
    # BLOCK PROCESSING (IF, REPEAT, FOR, WHILE, FUNCTIONS)
    # ---------------------------------------------------------
    def collect_block(self, bs):
        """Collect raw bits until the ending 110 marker."""
        chunk = ""
        depth = 1
        while True:
            op = bs.read(3)
            chunk += op
            if op == "101":  # nested block
                # add its type and keep nesting
                blk_type = bs.read(3)
                if(blk_type == "000" or blk_type == "110"):
                    blk_type += bs.read(10)
                elif(blk_type == "100" or blk_type == "011"):
                    blk_type += bs.read(4)
                    depth -= 1
                elif(blk_type == "101"):
                    mode = bs.read(1)
                    if(mode == "0"):
                        blk_type += mode + bs.read(12)
                    else:
                        blk_type += mode + bs.read(8)
                chunk += blk_type
                depth += 1
            elif op == "110":
                depth -= 1
                if depth == 0:
                    break
            else:
                # other opcodes: need to read their operands
                chunk += self.read_operands_for(op, bs)
        return chunk

    def read_operands_for(self, op, bs):
        """Reads correct operand bit count for a *non-block* opcode."""
        if op == "000": return ""
        if op == "001": return bs.read(3+4)
        if op == "010": return bs.read(3)
        if op == "011": 
            mode = bs.read(3)
            opnds = mode + bs.read(4)
            if(not mode == "101"):
                opnds+=bs.read(4)
            else:
                opnds+=bs.read(8)
            return opnds
        if op == "100": 
            mode = bs.read(2)
            if(int(mode, 2) < 3):
                return mode + bs.read(4)
            return mode + bs.read(8)
        if op == "111": 
            iocd = bs.read(2)
            if iocd == "10" or iocd == "11":
                return iocd + bs.read(4)
            return iocd
        return ""

    def handle_block(self, bs):
        """Processes a %blok instruction."""
        blk_type = self.read_int(bs.read(3))

        # ---------------------------------------------------------
        # 000 IF %addr %cond %addr … 110
        # ---------------------------------------------------------
        if blk_type == 0:
            a1 = self.read_int(bs.read(4))
            cond = self.read_int(bs.read(2))
            a2 = self.read_int(bs.read(4))
            body_bits = self.collect_block(bs)
            if self.cond(cond, a1, a2):
                self.run(BitStream(body_bits))

        # ---------------------------------------------------------
        # 001 REPEAT %addr … 110
        # ---------------------------------------------------------
        elif blk_type == 1:
            count = self.get(self.read_int(bs.read(4)))
            body_bits = self.collect_block(bs)
            for _ in range(count):
                self.run(BitStream(body_bits))

        # ---------------------------------------------------------
        # 010 function definition
        # ---------------------------------------------------------
        elif blk_type == 2:
            fid = self.read_int(bs.read(4))
            body_bits = self.collect_block(bs)
            self.functions[fid] = body_bits

        # ---------------------------------------------------------
        # 011 undefine function (immediate)
        # ---------------------------------------------------------
        elif blk_type == 3:
            fid = self.read_int(bs.read(4))
            self.functions[fid] = ""  # no-op

        # ---------------------------------------------------------
        # 100 call function (immediate, no block end)
        # ---------------------------------------------------------
        elif blk_type == 4:
            fid = self.read_int(bs.read(4))
            if fid in self.functions:
                self.run(BitStream(self.functions[fid]))

        # ---------------------------------------------------------
        # 101 FOR %addr %intg … 110
        # ---------------------------------------------------------
        elif blk_type == 5:
            mode = self.read_int(bs.read(1))
            addr = self.read_int(bs.read(4))
            if(mode == 0):
                count = self.read_int(bs.read(8))
            else:
                count = self.get(self.read_int(bs.read(4)))
            body_bits = self.collect_block(bs)
            for i in range(1, count+1):
                self.set(addr, i)
                self.run(BitStream(body_bits))

        # ---------------------------------------------------------
        # 110 WHILE %cond … 110
        # ---------------------------------------------------------
        elif blk_type == 6:
            adra = self.read_int(bs.read(4))
            cond = self.read_int(bs.read(2))
            adrb = self.read_int(bs.read(4))
            body_bits = self.collect_block(bs)
            while self.cond(cond, adra, adrb):
                self.run(BitStream(body_bits))

        # ---------------------------------------------------------
        # 111 UNASIGNED
        # ---------------------------------------------------------
        elif blk_type == 7:
            None


# =============================================================
# END OF VM
# =============================================================