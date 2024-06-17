"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import os
import sys
import typing
from SymbolTable import SymbolTable
from Parser import Parser
from Code import Code


def assemble_file(
        input_file: typing.TextIO, output_file: typing.TextIO) -> None:
    """Assembles a single file.

    Args:
        input_file (typing.TextIO): the file to assemble.
        output_file (typing.TextIO): writes all output to this file.
    """
    parser = Parser(input_file)
    symbol_table = SymbolTable()
    rom_count = 0

    # first pass
    while parser.has_more_commands():
        parser.advance()
        if parser.command_type() == "L_COMMAND":
            symbol_table.add_entry(parser.symbol(), rom_count)
        else:
            rom_count += 1

    # second pass
    symbol_count = 16
    parser.reset()
    while parser.has_more_commands():
        parser.advance()
        bin_str = ""
        if parser.command_type() == "A_COMMAND":
            curr_symbol = parser.symbol()
            address = -1
            if not curr_symbol.isdigit():
                if not (symbol_table.contains(curr_symbol)):   # check if the symbol was seen already and add him if not
                    symbol_table.add_entry(curr_symbol, symbol_count)
                    symbol_count += 1
                address = symbol_table.get_address(curr_symbol)     # get the address of the symbol
            else:
                address = int(curr_symbol)
            bin_str = str(bin(address)[2:].zfill(16))   # set the address to binary code
            output_file.write(bin_str + "\n")
        elif parser.command_type() == "C_COMMAND":
            dst = parser.dest()
            cmp = parser.comp()
            jmp = parser.jump()
            bin_str += Code.comp(cmp) + Code.dest(dst) + Code.jump(jmp)     # set the binary code of the C command
            output_file.write(bin_str + "\n")


if "__main__" == __name__:
    # Parses the input path and calls assemble_file on each input file.
    # This opens both the input and the output files!
    # Both are closed automatically when the code finishes running.
    # If the output file does not exist, it is created automatically in the
    # correct path, using the correct filename.
    if not len(sys.argv) == 2:
        sys.exit("Invalid usage, please use: Assembler <input path>")
    argument_path = os.path.abspath(sys.argv[1])
    if os.path.isdir(argument_path):
        files_to_assemble = [
            os.path.join(argument_path, filename)
            for filename in os.listdir(argument_path)]
    else:
        files_to_assemble = [argument_path]
    for input_path in files_to_assemble:
        filename, extension = os.path.splitext(input_path)
        if extension.lower() != ".asm":
            continue
        output_path = filename + ".hack"
        with open(input_path, 'r') as input_file, \
                open(output_path, 'w') as output_file:
            assemble_file(input_file, output_file)
