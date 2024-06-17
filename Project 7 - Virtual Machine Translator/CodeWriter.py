"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class CodeWriter:
    """Translates VM commands into Hack assembly code."""

    def __init__(self, output_stream: typing.TextIO) -> None:
        """Initializes the CodeWriter.

        Args:
            output_stream (typing.TextIO): output stream.
        """
        self.output_file = output_stream
        self.call_counter = 0
        self.label_counter = 0
        self.file_name = ""
        self.curr_func = ""

    def bootstrap(self) -> None:
        res = "// Bootstrap\n"
        res += "@256\n"
        res += "D=A\n"
        res += "@SP\n"
        res += "M=D\n"
        self.output_file.write(res)
        self.write_call("Sys.init", 0)

    def set_file_name(self, filename: str) -> None:
        """Informs the code writer that the translation of a new VM file is
        started.

        Args:
            filename (str): The name of the VM file.
        """
        self.file_name = filename

    def write_arithmetic(self, command: str) -> None:
        """Writes assembly code that is the translation of the given
        arithmetic command. For the commands eq, lt, gt, you should correctly
        compare between all numbers our computer supports, and we define the
        value "true" to be -1, and "false" to be 0.

        Args:
            command (str): an arithmetic command.
        """
        if command == "add":
            self.output_file.write(self.__add())
        elif command == "sub":
            self.output_file.write(self.__sub())
        elif command == "neg":
            self.output_file.write(self.__neg())
        elif command == "and":
            self.output_file.write(self.__and())
        elif command == "or":
            self.output_file.write(self.__or())
        elif command == "not":
            self.output_file.write(self.__not())
        elif command == "shiftleft":
            self.output_file.write(self.__shiftleft())
        elif command == "shiftright":
            self.output_file.write(self.__shiftright())
        elif command == "eq":
            self.output_file.write(self.__eq())
        elif command == "gt":
            self.output_file.write(self.__gt())
        elif command == "lt":
            self.output_file.write(self.__lt())

    def write_push_pop(self, command: str, segment: str, index: int) -> None:
        """Writes assembly code that is the translation of the given
        command, where command is either C_PUSH or C_POP.

        Args:
            command (str): "C_PUSH" or "C_POP".
            segment (str): the memory segment to operate on.
            index (int): the index in the memory segment.
        """
        if (segment == "pointer") or (segment == "temp") or (segment == "static"):
            self.__pushPopPointerTempStatic(command, segment, index)
        elif command == "C_PUSH":
            self.__pushSegment(segment, index)
        else:
            self.__popSegment(segment, index)

    def write_label(self, label: str) -> None:
        """Writes assembly code that affects the label command.
        Let "Xxx.foo" be a function within the file Xxx.vm. The handling of
        each "label bar" command within "Xxx.foo" generates and injects the symbol
        "Xxx.foo$bar" into the assembly code stream.
        When translating "goto bar" and "if-goto bar" commands within "foo",
        the label "Xxx.foo$bar" must be used instead of "bar".

        Args:
            label (str): the label to write.
        """
        label = self.file_name + "." + self.curr_func + "$" + label
        res = "// label\n"
        res += "(" + label + ")\n"
        self.output_file.write(res)

    def write_goto(self, label: str) -> None:
        """Writes assembly code that affects the goto command.

        Args:
            label (str): the label to go to.
        """
        label = self.file_name + "." + self.curr_func + "$" + label
        res = "// goto\n"
        res += "@" + label + "\n"
        res += "0;JMP\n"
        self.output_file.write(res)

    def write_if(self, label: str) -> None:
        """Writes assembly code that affects the if-goto command.

        Args:
            label (str): the label to go to.
        """
        label = self.file_name + "." + self.curr_func + "$" + label
        res = "// if-goto command\n"
        res += "@SP\n"
        res += "AM=M-1\n"
        res += "D=M\n"
        res += "@" + label + "\n"
        res += "D;JNE\n"
        self.output_file.write(res)

    def write_function(self, function_name: str, n_vars: int) -> None:
        """Writes assembly code that affects the function command.
        The handling of each "function Xxx.foo" command within the file Xxx.vm
        generates and injects a symbol "Xxx.foo" into the assembly code stream,
        that labels the entry-point to the function's code.
        In the subsequent assembly process, the assembler translates this
        symbol into the physical address where the function code starts.

        Args:
            function_name (str): the name of the function.
            n_vars (int): the number of local variables of the function.
        """
        self.curr_func = function_name
        res = "// function\n"
        res += "(" + function_name + ")\n"
        # push n_vars 0 values (initializes the callee's local variables)
        for i in range(n_vars):
            res += "@SP\n"
            res += "A=M\n"
            res += "M=0\n"
            res += "@SP\n"
            res += "M=M+1\n"
        self.output_file.write(res)

    def write_call(self, function_name: str, n_args: int) -> None:
        """Writes assembly code that affects the call command.
        Let "Xxx.foo" be a function within the file Xxx.vm.
        The handling of each "call" command within Xxx.foo's code generates and
        injects a symbol "Xxx.foo$ret.i" into the assembly code stream, where
        "i" is a running integer (one such symbol is generated for each "call"
        command within "Xxx.foo").
        This symbol is used to mark the return address within the caller's
        code. In the subsequent assembly process, the assembler translates this
        symbol into the physical memory address of the command immediately
        following the "call" command.

        Args:
            function_name (str): the name of the function to call.
            n_args (int): the number of arguments of the function.
        """
        self.call_counter += 1
        retAddr = self.file_name + "." + self.curr_func + "$ret." + str(self.call_counter)
        res = "// call " + function_name + "\n"
        # push return address, LCL, ARG, THIS, THAT
        for addr in [retAddr, "LCL", "ARG", "THIS", "THAT"]:
            res += "@" + addr + "\n"
            if addr == retAddr:
                res += "D=A\n"
            else:
                res += "D=M\n"
            res += "@SP\n"
            res += "A=M\n"
            res += "M=D\n"
            res += "@SP\n"
            res += "M=M+1\n"
        # ARG = SP - 5 - n_args
        res += "@" + str(n_args) + "\n"
        res += "D=A\n"
        res += "@5\n"
        res += "D=D+A\n"
        res += "@SP\n"
        res += "D=M-D\n"
        res += "@ARG\n"
        res += "M=D\n"
        # LCL = SP
        res += "@SP\n"
        res += "D=M\n"
        res += "@LCL\n"
        res += "M=D\n"
        # goto function and put return address label
        res += "@" + function_name + "\n"
        res += "0;JMP\n"
        res += "(" + retAddr + ")\n"
        self.output_file.write(res)

    def write_return(self) -> None:
        """Writes assembly code that affects the return command."""
        res = "// return\n"
        # frame = LCL
        res += "@LCL\n"
        res += "D=M\n"
        res += "@frame\n"
        res += "M=D\n"
        # return address = *(frame - 5)
        res += "@5\n"
        res += "A=D-A\n"
        res += "D=M\n"
        res += "@retAddr\n"
        res += "M=D\n"
        # *ARG = pop
        res += "@SP\n"
        res += "AM=M-1\n"
        res += "D=M\n"
        res += "@ARG\n"
        res += "A=M\n"
        res += "M=D\n"
        # SP = ARG + 1
        res += "D=A+1\n"
        res += "@SP\n"
        res += "M=D\n"
        # THAT = *(frame-1), THIS = *(frame-2), ARG = *(frame-3), LCL = *(frame-4)
        for addr in ["THAT", "THIS", "ARG", "LCL"]:
            res += "@frame\n"
            res += "AM=M-1\n"
            res += "D=M\n"
            res += "@" + addr + "\n"
            res += "M=D\n"
        # goto return address
        res += "@retAddr\n"
        res += "A=M\n"
        res += "0;JMP\n"
        self.output_file.write(res)

    ###########################################    Memory access commands    ###########################################
    def __pushSegment(self, segment: str, index: int) -> None:
        ind = str(index)
        seg_names = {"constant": "constant", "local": "LCL", "argument": "ARG", "this": "THIS", "that": "THAT"}
        res = "// push " + segment + " " + ind + "\n"
        seg = seg_names[segment]
        # D = index
        res += "@" + ind + "\n"
        res += "D=A\n"
        if segment != "constant":
            # D = RAM[seg + index]
            res += "@" + seg + "\n"
            res += "A=M+D\n"
            res += "D=M\n"
        # RAM[SP] = D
        res += "@SP\n"
        res += "A=M\n"
        res += "M=D\n"
        # SP++
        res += "@SP\n"
        res += "M=M+1\n"
        self.output_file.write(res)

    def __popSegment(self, segment: str, index: int) -> None:
        seg_names = {"local": "LCL", "argument": "ARG", "this": "THIS", "that": "THAT"}
        ind = str(index)
        res = "// pop " + segment + " " + ind + "\n"
        seg = seg_names[segment]
        #   RAM[R13] = segment + index
        res += "@" + ind + "\n"
        res += "D=A\n"
        res += "@" + seg + "\n"
        res += "D=M+D\n"
        res += "@R13\n"
        res += "M=D\n"
        #   SP--, D = RAM[SP]
        res += "@SP\n"
        res += "AM=M-1\n"
        res += "D=M\n"
        #   RAM[LCL + index] = D
        res += "@R13\n"
        res += "A=M\n"
        res += "M=D\n"
        self.output_file.write(res)

    def __pushPopPointerTempStatic(self, command: str, segment, index: int) -> None:
        if segment == "pointer":
            index += 3
        if segment == "temp":
            index += 5
        if segment != "static":
             ind = str(index)
        else:
            ind = self.file_name + "." + str(index)
        res = ""
        if command == "C_PUSH":
            res += "// push " + segment + " " + ind + "\n"
            #   D = pointer/temp + index/ static i
            res += "@" + ind + "\n"
            res += "D=M\n"
            #   RAM[SP] = D
            res += "@SP\n"
            res += "A=M\n"
            res += "M=D\n"
            #   SP++
            res += "@SP\n"
            res += "M=M+1\n"
        else:   # command = "C_POP"
            res += "// pop " + segment + " " + ind + "\n"
            #   SP--, D = RAM[SP]
            res += "@SP\n"
            res += "AM=M-1\n"
            res += "D=M\n"
            #   pointer/temp + index/ static i = D
            res += "@" + ind + "\n"
            res += "M=D\n"
        self.output_file.write(res)

    ##########################################   Stack arithmetic commands   ###########################################
    def __add(self) -> str:
        res = "// add\n"
        res += "@SP\n"
        res += "AM=M-1\n"
        res += "D=M\n"
        res += "A=A-1\n"
        res += "M=M+D\n"
        return res

    def __sub(self) -> str:
        res = "// sub\n"
        res += "@SP\n"
        res += "AM=M-1\n"
        res += "D=M\n"
        res += "A=A-1\n"
        res += "M=M-D\n"
        return res

    def __neg(self) -> str:
        res = "// neg\n"
        res += "@SP\n"
        res += "A=M-1\n"
        res += "M=-M\n"
        return res

    def __and(self) -> str:
        res = "// and\n"
        res += "@SP\n"
        res += "AM=M-1\n"
        res += "D=M\n"
        res += "A=A-1\n"
        res += "M=M&D\n"
        return res

    def __or(self) -> str:
        res = "// or\n"
        res += "@SP\n"
        res += "AM=M-1\n"
        res += "D=M\n"
        res += "A=A-1\n"
        res += "M=M|D\n"
        return res

    def __not(self) -> str:
        res = "// not\n"
        res += "@SP\n"
        res += "A=M-1\n"
        res += "M=!M\n"
        return res

    def __shiftleft(self) -> str:
        res = "// shiftleft\n"
        res += "@SP\n"
        res += "A=M-1\n"
        res += "M=M<<\n"
        return res

    def __shiftright(self) -> str:
        res = "// shiftright\n"
        res += "@SP\n"
        res += "A=M-1\n"
        res += "M=M>>\n"
        return res

    def __eq(self) -> str:
        self.label_counter += 1
        label = "_" + self.file_name + "." + self.curr_func + str(self.label_counter)
        res = "// eq_" + label + "\n"
        res += "@SP\n"
        res += "AM=M-1\n"
        res += "D=M\n"
        res += "A=A-1\n"
        res += "D=M-D\n"
        res += "M=-1\n"
        res += "@CONTINUE" + label + "\n"  # x == y
        res += "D;JEQ\n"
        res += "@SP\n"
        res += "A=M-1\n"
        res += "M=0\n"  # x != y
        res += "(CONTINUE" + label + ")\n"
        return res

    def __gt(self) -> str:
        self.label_counter += 1
        label = "_" + self.file_name + "." + self.curr_func + str(self.label_counter)
        res = "// gt_" + label + "\n"
        #   RAM[R13] = x
        res += "@SP\n"
        res += "A=M-1\n"
        res += "A=A-1\n"
        res += "D=M\n"
        res += "@R13\n"
        res += "M=D\n"
        #   RAM[R14] = y
        res += "@SP\n"
        res += "AM=M-1\n"
        res += "D=M\n"
        res += "@R14\n"
        res += "M=D\n"
        res += "@YPOSITIVE" + label + "\n"
        res += "D;JGT\n"
        #   y < 0
        res += "@R13\n"
        res += "D=M\n"
        res += "@ENDGT" + label + "\n"    # y < 0 and x > 0   ==>   x > y  (true)
        res += "D;JGT\n"
        #   x and y have the same sign
        res += "(SAMESIGN" + label + ")\n"
        res += "@R13\n"
        res += "D=M\n"
        res += "@R14\n"
        res += "D=D-M\n"
        res += "@ENDGT" + label + "\n"
        res += "D;JGT\n"
        res += "@ENDNOGT" + label + "\n"
        res += "0;JMP\n"
        #   y > 0
        res += "(YPOSITIVE" + label + ")\n"
        res += "@R13\n"
        res += "D=M\n"
        res += "@SAMESIGN" + label + "\n"
        res += "D;JGT\n"
        #   return false (0)
        res += "(ENDNOGT" + label + ")\n"
        res += "@SP\n"
        res += "A=M-1\n"
        res += "M=0\n"
        res += "@CONTINUE" + label + "\n"
        res += "0;JMP\n"
        #   return true (-1)
        res += "(ENDGT" + label + ")\n"
        res += "@SP\n"
        res += "A=M-1\n"
        res += "M=-1\n"
        res += "(CONTINUE" + label + ")\n"
        return res

    def __lt(self) -> str:
        self.label_counter += 1
        label = "_" + self.file_name + "." + self.curr_func + str(self.label_counter)
        res = "// lt_" + label + "\n"
        #   RAM[R13] = x
        res += "@SP\n"
        res += "A=M-1\n"
        res += "A=A-1\n"
        res += "D=M\n"
        res += "@R13\n"
        res += "M=D\n"
        #   RAM[R14] = y
        res += "@SP\n"
        res += "AM=M-1\n"
        res += "D=M\n"
        res += "@R14\n"
        res += "M=D\n"
        res += "@YNEGATIVE" + label + "\n"
        res += "D;JLT\n"
        #   y > 0
        res += "@R13\n"
        res += "D=M\n"
        res += "@ENDLT" + label + "\n"    # y > 0 and x < 0   ==>    x < y (true)
        res += "D;JLT\n"
        #   x and y have the same sign
        res += "(SAMESIGN" + label + ")\n"
        res += "@R13\n"
        res += "D=M\n"
        res += "@R14\n"
        res += "D=D-M\n"
        res += "@ENDLT" + label + "\n"
        res += "D;JLT\n"
        res += "@ENDNOLT" + label + "\n"
        res += "0;JMP\n"
        #   y < 0
        res += "(YNEGATIVE" + label + ")\n"
        res += "@R13\n"
        res += "D=M\n"
        res += "@SAMESIGN" + label + "\n"
        res += "D;JLT\n"
        #   return false (0)
        res += "(ENDNOLT" + label + ")\n"
        res += "@SP\n"
        res += "A=M-1\n"
        res += "M=0\n"
        res += "@CONTINUE" + label + "\n"
        res += "0;JMP\n"
        #   return true (-1)
        res += "(ENDLT" + label + ")\n"
        res += "@SP\n"
        res += "A=M-1\n"
        res += "M=-1\n"
        res += "(CONTINUE" + label + ")\n"
        return res
