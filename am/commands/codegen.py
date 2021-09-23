# coding: utf-8
import json

from am.commands import cmd
from am.turing_machine import BLANK


@cmd(
    ("-i", "--input", "fill the first tape with standard input", None, "store_true"),
    ("-v", "--verbose", "display status information at each iteration", None, "store_true"),
)
def codegen(am, input, verbose, **kwargs):
    """
    Generates a C implementation of an automatic machine.
    """
    states = {state: (i, transitions) for i, (state, transitions) in enumerate(am.transitions.items())}
    end_states = {state: (-1 - i, message) for i, (state, message) in enumerate(am.end_states.items())}
    all_states = {**states, **end_states}

    print(f"""
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const char BLANK = '{BLANK}';

typedef struct
{{
    char* buf;
    size_t size;
    ssize_t position;
}} Tape;

typedef int state_t;

Tape tapes[{am.nb_tapes}];

char tape_read(size_t tape_num)
{{
    const Tape* tape = &tapes[tape_num];
    
    if (tape->position < 0 || tape->position >= tape->size)
        return BLANK;
          
    return tape->buf[tape->position];
}}

void tape_write(size_t tape_num, char symbol)
{{
    Tape* tape = &tapes[tape_num];
    
    if (tape->position < 0)
    {{
        size_t newsize = tape->size - tape->position;
        char* newbuf = malloc(newsize);
        memcpy(newbuf - tape->position, tape->buf, tape->size);
        memset(newbuf, BLANK, -tape->position);
        free(tape->buf);
        tape->buf = newbuf; 
        tape->position = 0;
        tape->size = newsize;
    }}
    else if (tape->position >= tape->size)
    {{
        size_t newsize = tape->position + 1;
        char* newbuf = malloc(newsize);
        memcpy(newbuf, tape->buf, tape->size);
        memset(newbuf + tape->size, BLANK, newsize - tape->size);
        free(tape->buf);
        tape->buf = newbuf;
        tape->size = newsize;
    }}
    
    tape->buf[tape->position] = symbol;
}}

#define BUF_SIZE 256
#define MIN(a,b) (((a)<(b))?(a):(b))
#define MAX(a,b) (((a)>(b))?(a):(b))

void display(state_t current)
{{
    printf("Current state : %d\\n", current);
    for (size_t num = 0; num < {am.nb_tapes}; num++)
    {{
        printf("Tape %2zu : %.*s\\n", num, (int) tapes[num].size, tapes[num].buf);
    }}
    fflush(stdout);
}}

#define SHOW_STEP() fprintf(stderr, "Step count: %zu\\n", step)

int main()
{{
    for (int i = 0; i < {am.nb_tapes}; i++)
    {{
        tapes[i] = (Tape){{ .buf = NULL, .size = 0, .position = 0 }};
    }}""")

    if input:
        print("""
    size_t input_size = 0;
    size_t current_size = BUF_SIZE;
    char* input_buf = malloc(current_size);
    memset(input_buf, BLANK, current_size);
    size_t read;
    while ((read = fread(input_buf + input_size, 1, current_size - input_size, stdin)) > 0)
    {
        input_size += read;
        if (current_size - input_size < 16)
        {
            input_buf = realloc(input_buf, current_size += BUF_SIZE);
        }
    }
    
    input_buf = realloc(input_buf, input_size);
    
    tapes[0] = (Tape){ .buf = input_buf, .size = input_size, .position = 0 };""")
    print(f"""
    state_t current = {all_states[am.initial_state][0]};
    
    for (size_t step = 0; ; step++)
    {{""")
    if verbose:
        print(f"""
        display(current);""")
    print(f"""
        char tape_values[] = {{ {", ".join(f"tape_read({tape})" for tape in range(am.nb_tapes))} }};
        switch (current)
        {{""")

    for state, (number, message) in end_states.items():
        print(f"""
        case {number}: // {state}
            display(current);
            SHOW_STEP();
            fprintf(stderr, "END STATE '%s': %s\\n", {json.dumps(state)}, {json.dumps(message)});
            return EXIT_SUCCESS;
        """)

    for state, (number, transitions) in states.items():
        print(f"""
        case {number}: // {state}""")
        for i, (read, (write, moves, next_state)) in enumerate(transitions.items()):
            print(f"""
            {"else " if i != 0 else ""}if ({" && ".join(f"tape_values[{tape}] == '{value}'" for tape, value in enumerate(read))})
            {{
                {"; ".join(f"tape_write({tape}, '{value}')" for tape, value in enumerate(write))};
                {"; ".join(f"tapes[{tape}].position += {delta}" for tape, delta in enumerate(moves))};
                current = {all_states[next_state][0]};
            }}""")
        print(f"""
            else
            {{
                SHOW_STEP();
                goto ERROR;
            }}
            
            break;""")
    print(f"""
        default:
            SHOW_STEP();
            fprintf(stderr, "UNKNOWN STATE '%d'\\n", current);
            return EXIT_FAILURE;
        }}
    }}
    
ERROR:
    fprintf(stderr, "MISSING TRANSITION FROM STATE '%d'\\n", current);
    return EXIT_FAILURE;
}}
""")