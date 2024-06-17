"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class Parser:
    """Encapsulates access to the input code. Reads an assembly program
    by reading each command line-by-line, parses the current command,
    and provides convenient access to the commands components (fields
    and symbols). In addition, removes all white space and comments.
    """

    def __init__(self, input_file: typing.TextIO) -> None:
        """Opens the input file and gets ready to parse it.

        Args:
            input_file (typing.TextIO): input file.
        """
        file = input_file.read().splitlines()
        temp = []
        for line in file:
            line = line.replace(" ", "")
            if (line == "") or (line[0] == '/'):
                continue
            end_line = len(line)
            if '/' in line:
                end_line = line.index('/')
            temp.append(line[:end_line])
        self.commands = temp
        self.curr_command = ""
        self.counter = 0

    def has_more_commands(self) -> bool:
        """Are there more commands in the input?

        Returns:
            bool: True if there are more commands, False otherwise.
        """
        return self.counter < len(self.commands)

    def advance(self) -> None:
        """Reads the next command from the input and makes it the current command.
        Should be called only if has_more_commands() is true.
        """
        self.curr_command = self.commands[self.counter]
        self.counter += 1

    def command_type(self) -> str:
        """
        Returns:
            str: the type of the current command:
            "A_COMMAND" for @Xxx where Xxx is either a symbol or a decimal number
            "C_COMMAND" for dest=comp;jump
            "L_COMMAND" (actually, pseudo-command) for (Xxx) where Xxx is a symbol
        """
        if self.curr_command[0] == '@':
            return "A_COMMAND"
        if self.curr_command[0] == '(':
            return "L_COMMAND"
        return "C_COMMAND"

    def symbol(self) -> str:
        """
        Returns:
            str: the symbol or decimal Xxx of the current command @Xxx or
            (Xxx). Should be called only when command_type() is "A_COMMAND" or 
            "L_COMMAND".
        """
        if self.curr_command[0] == "@":
            return self.curr_command[1:]
        return self.curr_command[1:-1]

    def dest(self) -> str:
        """
        Returns:
            str: the dest mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        ind = self.curr_command.find('=')
        if ind == -1:
            return "NULL"
        return self.curr_command[:ind]

    def comp(self) -> str:
        """
        Returns:
            str: the comp mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        left = self.curr_command.find('=') + 1
        if ';' in self.curr_command:
            return self.curr_command[left:self.curr_command.index(';')]
        return self.curr_command[left:]

    def jump(self) -> str:
        """
        Returns:
            str: the jump mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        if ';' in self.curr_command:
            return self.curr_command[self.curr_command.index(';')+1:]
        return "NULL"

    def reset(self) -> None:
        self.counter = 0
        self.curr_command = ""