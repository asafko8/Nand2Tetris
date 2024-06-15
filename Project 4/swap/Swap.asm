// This file is part of nand2tetris, as taught in The Hebrew University, and
// was written by Aviv Yaish. It is an extension to the specifications given
// [here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
// as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
// Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).

// The program should swap between the max. and min. elements of an array.
// Assumptions:
// - The array's start address is stored in R14, and R15 contains its length
// - Each array value x is between -16384 < x < 16384
// - The address in R14 is at least >= 2048
// - R14 + R15 <= 16383
//
// Requirements:
// - Changing R14, R15 is not allowed.

// goto infinite loop if the array length is less than 2. 
@R15
D = M - 1
@END
D;JLE
// initializes min, max to the first object in the array. pointer to the second
@R14
D = M
@pointer
M = D + 1
@min
M = D
@max
M = D
(LOOP)
    // check min
    @pointer
    A = M
    D = M
    @min
    A = M
    D = D - M
    @SWAPMIN
    D;JLT
    // check max
    @pointer
    A = M
    D = M
    @max
    A = M
    D = D - M
    @SWAPMAX
    D;JGT
    (LOOPCON) // continuation of the loop
    @pointer
    M = M + 1
    // check if end of the array
    @R14
    D = M
    @R15
    D = D + M
    @pointer
    D = D - M
    @SWAP
    D;JEQ
    @LOOP
    0;JMP

(SWAPMIN)
    @pointer
    D = M
    @min
    M = D
    @LOOPCON
    0;JMP

(SWAPMAX)
    @pointer
    D = M
    @max
    M = D
    @LOOPCON
    0;JMP

(SWAP)
    // save min in temp
    @min
    A = M
    D = M
    @temp
    M = D
    //change min to max
    @max
    A = M
    D = M
    @min
    A = M
    M = D
    // change max to temp (min)
    @temp
    D = M
    @max
    A = M
    M = D

(END)
    @END
    0;JMP