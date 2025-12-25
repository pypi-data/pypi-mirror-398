import sys

# =============================================================
#           SmolBit → C TRANSPILER (BITSTREAM VERSION)
# =============================================================

class BitStream:
    def __init__(self, bits: str):
        self.bits = bits.replace(" ", "").replace("\n", "")
        self.pos = 0

    def read(self, n):
        if self.pos + n > len(self.bits):
            raise RuntimeError("Unexpected EOF while reading bitcode")
        out = self.bits[self.pos:self.pos+n]
        self.pos += n
        return out

    def peek(self, n):
        if self.pos + n > len(self.bits):
            raise RuntimeError("Unexpected EOF while peeking")
        return self.bits[self.pos:self.pos+n]

    def eof(self):
        return self.pos >= len(self.bits)


# =============================================================
#                 TRANSPILER ENGINE
# =============================================================

class Transpiler:
    def __init__(self, bitcode: str):
        self.bs = BitStream(bitcode)
        self.c_code = []
        self.indent_level = 1
        self.functions = {}  # id -> C code string

        self.loop_counter = 0
        self.temp_counter = 0

    def indent(self):
        return "    " * self.indent_level

    def emit(self, line):
        self.c_code.append(self.indent() + line)

    def read_int(self, bits):
        return int(bits, 2)

    def unique(self, prefix):
        self.temp_counter += 1
        return f"{prefix}_{self.temp_counter}"

    # ---------------------------------------------------------
    # MAIN DISPATCH
    # ---------------------------------------------------------

    def transpile(self, bs=None):
        if bs is None:
            bs = self.bs

        while not bs.eof():
            op = bs.read(3)

            if op == "000":  # NOP
                continue

            elif op == "001":  # MNIP
                mnip = self.read_int(bs.read(2))
                addr = self.read_int(bs.read(4))
                self.handle_mnip(mnip, addr)

            elif op == "010":  # PAGE SWITCH
                page = self.read_int(bs.read(2))
                self.emit(f"page = {page};")

            elif op == "011":  # ARITHMETIC
                mode = self.read_int(bs.read(3))
                a1 = self.read_int(bs.read(4))
                a2 = self.read_int(bs.read(4))
                self.handle_arith(mode, a1, a2)

            elif op == "100":  # DISPLAY
                mode = self.read_int(bs.read(2))
                addr = self.read_int(bs.read(4))
                self.handle_display(addr, mode)

            elif op == "101":  # BLOCK INSTRUCTION
                blk_type = self.read_int(bs.read(3))
                self.handle_block(blk_type, bs)

            elif op == "110":  # BLOCK END
                return

            elif op == "111":  # IO CODE
                self.handle_iocd(bs)

        return

    # ---------------------------------------------------------
    # Helpers to decode operand sets for nested block collection
    # ---------------------------------------------------------

    def read_operands(self, op, bs):
        if op == "000": return ""
        if op == "001": return bs.read(2+4)
        if op == "010": return bs.read(2)
        if op == "011": return bs.read(3+4+4)
        if op == "100": return bs.read(4+2)
        if op == "111":
            i = bs.read(2)
            if i in ("10", "11"):
                return i + bs.read(4)
            return i
        return ""

    def collect_block_bits(self, bs):
        """Collects all bits between a 101 … 110 block, inclusive of nested blocks."""
        bits = ""
        depth = 1

        while True:
            op = bs.read(3)
            bits += op

            if op == "101":
                blk = bs.read(3)
                bits += blk
                depth += 1

            elif op == "110":
                depth -= 1
                if depth == 0:
                    break

            else:
                ops = self.read_operands(op, bs)
                bits += ops

        return bits

    # ---------------------------------------------------------
    # MNIP translation
    # ---------------------------------------------------------

    def handle_mnip(self, mnip, addr):
        if mnip == 0:
            self.emit(f"pages[page][{addr}] = (pages[page][{addr}] + 1) & 0xFF;")
        elif mnip == 1:
            self.emit(f"pages[page][{addr}] = (pages[page][{addr}] - 1) & 0xFF;")
        elif mnip == 2:
            self.emit(f"pages[page][{addr}] = 0;")
        elif mnip == 3:
            self.emit(f"pages[page][{addr}] = {addr};")

    # ---------------------------------------------------------
    # Arithmetic translation
    # ---------------------------------------------------------

    def handle_arith(self, mode, a1, a2):
        if mode == 0:
            self.emit(f"pages[page][{a1}] = (pages[page][{a1}] + pages[page][{a2}]) & 0xFF;")
        elif mode == 1:
            self.emit(f"pages[page][{a1}] = (pages[page][{a1}] - pages[page][{a2}]) & 0xFF;")
        elif mode == 2:
            self.emit(f"pages[page][{a1}] = (pages[page][{a1}] * pages[page][{a2}]) & 0xFF;")
        elif mode == 3:
            self.emit(f"pages[page][{a1}] = (pages[page][{a1}] / (pages[page][{a2}] ? pages[page][{a2}] : 1)) & 0xFF;")
        elif mode == 4:
            self.emit(f"pages[page][{a1}] = pages[page][{a2}];")
        elif mode == 5:
            self.emit(f"pages[page][{a1}] = 255;")
        elif mode == 6:
            self.emit(f"pages[page][{a1}] = (int)pow(pages[page][{a1}], pages[page][{a2}]);")
        elif mode == 7:
            self.emit(f"pages[page][{a1}] = (int)pow(pages[page][{a1}], 1.0 / (pages[page][{a2}] ? pages[page][{a2}] : 1));")

    # ---------------------------------------------------------
    # Display translation
    # ---------------------------------------------------------

    def handle_display(self, addr, mode):
        if mode == 0:
            self.emit(f'printf(\"%08b\", pages[page][{addr}]);')
        elif mode == 1:
            self.emit(f'printf(\"%d\\n\", pages[page][{addr}]);')
        elif mode == 2:
            self.emit(f'printf(\"%X\\n\", pages[page][{addr}]);')
        elif mode == 3:
            self.emit(f'putchar(pages[page][{addr}]);')

    # ---------------------------------------------------------
    # IO CODES
    # ---------------------------------------------------------

    def handle_iocd(self, bs):
        code = self.read_int(bs.read(2))

        if code == 0:
            self.emit("return 0;")
        elif code == 1:
            self.emit("return 1;")

        elif code == 2:  # read hex
            addr = self.read_int(bs.read(4))
            self.emit(f"scanf(\"%x\", &pages[page][{addr}]);")

        elif code == 3:  # read bin
            addr = self.read_int(bs.read(4))
            temp = self.unique("binbuf")
            self.emit(f"char {temp}[32]; scanf(\"%s\", {temp});")
            self.emit(f"pages[page][{addr}] = strtol({temp}, NULL, 2);")

    # ---------------------------------------------------------
    # BLOCK HANDLING
    # ---------------------------------------------------------

    def handle_block(self, blk, bs):
        # ---------------------------------------------------------
        # IF %addr %cond %addr … 110
        # ---------------------------------------------------------
        if blk == 0:
            a1 = self.read_int(bs.read(4))
            cond = self.read_int(bs.read(2))
            a2 = self.read_int(bs.read(4))
            body = self.collect_block_bits(bs)

            ccond = ["==", "<=", ">=", "!="][cond]
            self.emit(f"if (pages[page][{a1}] {ccond} pages[page][{a2}]) {{")
            self.indent_level += 1
            self.transpile(BitStream(body))
            self.indent_level -= 1
            self.emit("}")

        # ---------------------------------------------------------
        # REPEAT %intg … 110
        # ---------------------------------------------------------
        elif blk == 1:
            count = self.read_int(bs.read(4))
            body = self.collect_block_bits(bs)
            ivar = self.unique("i")
            self.emit(f"for (int {ivar}=0; {ivar}<{count}; {ivar}++) {{")
            self.indent_level += 1
            self.transpile(BitStream(body))
            self.indent_level -= 1
            self.emit("}")

        # ---------------------------------------------------------
        # FUNCTION DEF
        # ---------------------------------------------------------
        elif blk == 2:
            fid = self.read_int(bs.read(4))
            body = self.collect_block_bits(bs)
            # store raw bits to compile after full pass
            self.functions[fid] = body

        # ---------------------------------------------------------
        # UNDEFINE
        # ---------------------------------------------------------
        elif blk == 3:
            fid = self.read_int(bs.read(4))
            self.functions[fid] = ""

        # ---------------------------------------------------------
        # CALL (IMMEDIATE)
        # ---------------------------------------------------------
        elif blk == 4:
            fid = self.read_int(bs.read(4))
            self.emit(f"func_{fid}();")

        # ---------------------------------------------------------
        # FOR %addr %intg … 110
        # ---------------------------------------------------------
        elif blk == 5:
            addr = self.read_int(bs.read(4))
            count = self.read_int(bs.read(4))
            body = self.collect_block_bits(bs)
            ivar = self.unique("j")
            self.emit(f"for (int {ivar}=1; {ivar}<={count}; {ivar}++) {{")
            self.indent_level += 1
            self.emit(f"pages[page][{addr}] = {ivar};")
            self.transpile(BitStream(body))
            self.indent_level -= 1
            self.emit("}")

        # ---------------------------------------------------------
        # WHILE %cond … 110
        # ---------------------------------------------------------
        elif blk == 6:
            cond = self.read_int(bs.read(2))
            body = self.collect_block_bits(bs)
            cc = ["==", "<=", ">=", "!="][cond]
            # assume v0 and v1 like VM
            self.emit(f"while (pages[page][0] {cc} pages[page][1]) {{")
            self.indent_level += 1
            self.transpile(BitStream(body))
            self.indent_level -= 1
            self.emit("}")

        # ---------------------------------------------------------
        # COMMENT (skip bits)
        # ---------------------------------------------------------
        elif blk == 7:
            n = self.read_int(bs.read(8))
            bs.read(n)  # skip

    # ---------------------------------------------------------
    # ASSEMBLE FINAL C CODE
    # ---------------------------------------------------------

    def generate_final_c(self):
        out = []

        # includes
        out.append("#include <stdio.h>")
        out.append("#include <stdlib.h>")
        out.append("#include <math.h>")
        out.append("")
        out.append("unsigned char pages[4][16] = {")
        out.append("    {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15},")
        out.append("    {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15},")
        out.append("    {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15},")
        out.append("    {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}")
        out.append("};")
        out.append("int page = 0;")
        out.append("")

        # generate function bodies
        for fid, bits in self.functions.items():
            out.append(f"void func_{fid}() {{")
            self.indent_level = 1
            temp = self.c_code
            self.c_code = []
            self.transpile(BitStream(bits))
            out.extend(self.c_code)
            self.c_code = temp
            out.append("}")
            out.append("")

        # main function
        out.append("int main() {")
        out.extend(self.c_code)
        out.append("}")
        return "\n".join(out)


# =============================================================
# CLI USAGE
# =============================================================

if __name__ == "__main__":
    bitcode = sys.stdin.read()
    T = Transpiler(bitcode)
    T.transpile()
    print(T.generate_final_c())
