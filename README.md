# Automatic Machines Simulator

Simulator for Turing Machines, in Python 3, by Christophe Papazian.
Visualisation of the simulation is done with the curses library.

### Changelog :
V1.2 2019/09/19 : Github repository and refactorisation of the code

                  Drawing Feature added on 09/23

V1.1 2018/10/30 : Added support for non color terminal and
                  refactor the code in am_curses.py

## A. Installation
You need to install
 - python (at least 3.6)
 - ply (3.11)
 - graphviz version 2.40.1 (for the draw command)

 you can easily install ply using pip with something like
```
 % sudo -H python -m pip install ply
```
## B. Usage

 Create a file containing the description of your machines.
 An exemple is provided within TD1.txt (only available to students after the end of TD1) that contains :
  - machine TD1.1 : one tape. It recognizes words "a=b+c"
    with a,b and c binary numbers using 0,1.
  - machine TD1.2 : one tape. It recognizes words "ww"
    with w a non empty binary word using 0,1.
  - machine TD1.3 : two tapes. Same as previous, but better complexity.
  - machine TD1.4 : two tapes. It recognizes words "a^n" with
    n a positive square.
  - machine TD1.5a : two tapes. It writes on tape 2 the binary length of
    the binary word on tape 1.

### B.1 Syntax :
 - All states begin with `@` and use letters, digits or underscore (`@OK` `@VERY_LONG_NAME`)
 - All letters (on the tape) begin with `'` followed by one unicode character.
 - The special blank letter uses an underscore : `'_`
 - Comments begin with `#` and end with end of line.

```
 NEW machine_name number_of_tapes
 START initial_state
 
 # You can specify as many end states as you want. Usually one is enough.
 END end_state result [second_end_state second_result [and so on]]
 
 # You can specify a special end state that will be reached in case
 # an unknown transition is obtained (ERROR state by default)
 UNDEFINED undefined_state undefined_result
 
 # Then you specify the transitions
 FROM state # state you're in.
 read write move new_state # what you read and then write, move and new state
 read write move new_state
 
 # write is optional. If not specified, tapes are left unchanged.
 # new_state is optional. If not specified, the machine stays in the same state.

 # this is an error to specify for one state, the same letter in reading position
 # more than once
```

 example with a two tape machine. Moves are `L` for left, `R` for right and `S` for stay.
```
 FROM @I
 '0,'0 '0,'0 L,S @I
 '1,'0 '0,'1 L,S @I
```
 can be written as:
```
 FROM @I
 '0,'0 L,S
 '1,'0 '0,'1 L,S
```
 You can also use alternatives to specify read and write.  For example:
```
 FROM @I
 '1,'0 '2,'1 L,L @I
 '0,'1 '1,'1 L,L @I
 '2,'2 '0,'1 L,L @I
```
 can be written as:
```
 FROM @I
 '1|'0|'2,'0|'1|'2 '2|'1|'0,'1 L,L
```

### B.2 Use the simulator
 Only the first tape can be specified. All other tapes begin empty with blank only.

 The initial position of the head is the character between angle brackets  `<?>` on the tape. 
 Otherwise the head is placed on the left most character.

 Examples:
 - launch the machine TD1.1 on the tape "1100=101+111" :
```
 % python -m am simulate TD1.txt -n TD1.1 -t "1100=101+111"
 % python -m am simulate TD1.txt -n TD1.2 -t "11001100"
 % python -m am simulate TD1.txt -n TD1.3 -t "11001100"
 % python -m am simulate TD1.txt -n TD1.4 -t "aaaaaaaaaaaaaaaa"
 % python -m am simulate TD1.txt -n TD1.5a -t "0101100011101011100010"
```

 While in simulation :

 **simulation starts in pause mode. You need to press a key (like space) to advance one step.**

 special keys :
 - `+`/`-` : increase or decrease speed. Typing + while in pause mode exit pause and start
     with a speed of 4 steps by second.
 - `p` : return to pause mode
 - `b` : pause mode and go one step backward.
 - `e` : maximum speed to quickly go to the end of the computation.

      IT WILL CRASH IF YOUR COMPUTATION IS WITHOUT END !!!!
 - `q` : quit
 - `r` : restart

 The simulation returns to pause mode when an end state is reached.
 In that last case, any key will exit the simulation, except b.

 possible option pour am_curses.py :
```
  -h, --help            show this help message and exit
  -t TAPE, --tape TAPE  initial tape. First position inside angle brackets <.>
  -n NAME, --name NAME  name of the machine used
  -r, --result-only     no simulation, result only
  -s, --statistics      print detailed statistics
```

### B.3 Draw your machine
YOU NEED TO INSTALL GRAPHVIZ FOR THIS FEATURE

As a new feature (on 2019/09/23), you can now draw your machines. 
```
 % python -m am draw TD1.txt -n TD1.1
```

It will generate a pdf file (with the same filename as the machine name) from the description of the machine.



 ## C.Final Notes
  If your machine doesn't stop, it will not stop. Sorry !

  The simulator supports up to 7 tapes now. The lexer/parser supports any number of tapes.

  PUBLIC DOMAIN. IT'S FREE.

  USE AT YOUR OWN RISK.

  Do whatever you want with the code.
