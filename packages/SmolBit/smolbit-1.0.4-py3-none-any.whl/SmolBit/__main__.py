from .smolbitCore import *
from .Converter import *
from .Transpiler import *
import sys
if __name__ == "__main__":
    if sys.argv[1] == "run":
        bitcode = sys.argv[2]
        vm = VM(bitcode)
        vm.run()
    elif sys.argv[1] == "compile":
        path = sys.argv[2]
        save = sys.argv[3]
        with open(path, "r") as file:
            bits = file.read()
        convert(bits, save)