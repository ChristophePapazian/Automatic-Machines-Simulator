# V1.2 2019/09/19 Christophe Papazian

import argparse
import json
import subprocess
from collections import defaultdict
from sys import argv, exit, stdout

from am.am_curses import UI_Curses
from am.am_parser import am_from_string
from am.turing_machine import Simulation, BLANK

COMMANDS = {}


def cmd(*args):
    def inner(fct):
        COMMANDS[fct.__name__] = args, fct
        return fct

    return inner


@cmd(
    ("-t", "--tape", "initial tape. First position inside angle brackets <.>", "<_>", None),
    ("-r", "--result-only", "no simulation, result only", None, "store_true"),
    ("-s", "--statistics", "print detailed statistics", None, "store_true")
)
def simulate(am, tape, result_only, statistics, **kwargs):
    """
    Simulate the Turing machine
    """
    sim = Simulation(am, tape)
    if result_only:
        while sim.result is None:
            sim.step()
    else:
        UI_Curses(sim)

    if statistics:
        res_t, res_s = defaultdict(lambda: 0), defaultdict(lambda: 0)
        for s, (h, _) in zip(sim.history, sim.tape.history):
            res_t[(s, h)] += 1
            res_s[s] += 1
        res_t = [(res_t[(s, h)], s, h) for (s, h) in res_t]
        res_s = [(res_s[s], s) for s in res_s]
        res_t.sort(reverse=True)
        res_s.sort(reverse=True)
        print('By transitions:')
        for r, s, h in res_t:
            print('%12s' % s, ','.join(h), ':%4d' % r)
        print('By states:')
        for r, s in res_s:
            print('%12s' % s, ':%4d' % r)
    for i in range(am.nb_tapes):
        print(''.join(sim.tape.stacks[0][i]), '<' + sim.tape.head[i] +
              '>', ''.join(reversed(sim.tape.stacks[1][i])), sep='')
    print(f"{sim.result} in {sim.steps} steps.")


@cmd()
def draw(am, file=None, **kwargs):
    """
        Create a pdf file from an automatic machine.
        Requirement : the dot program from GraphViz
        """
    DOT_DATA = []
    D = {-1: "L", 0: "S", 1: "R"}
    if file is None: file = stdout
    DOT_DATA.append("digraph {")
    DOT_DATA.append(" graph [mclimit = 100 rankdir = LR]")
    # print(' edge [lblstyle="sloped"];')
    DOT_DATA.append(' QI0123456789 [shape=point]')
    DOT_DATA.append(f' QI0123456789 -> {am.initial_state}')
    for s in am.transitions:
        loops = []
        T = defaultdict(list)
        color = ["white", "0.333 0.5 1.0", "0.0 0.25 1.0", "0.1666 0.75 1.0"][
            int(s == am.initial_state) + 2 * int(s in am.end_states)]
        options = f'fillcolor="{color}"'
        DOT_DATA.append(f'"{s}" [style="filled" {options}]')
        for r in am.transitions[s]:
            w, m, ns = am.transitions[s][r]
            T[(m, ns)].append((r, w))
        for m, ns in T:
            r, w = zip(*T[(m, ns)])
            R = '<font color="blue">|</font>'.join(",".join(ro) for ro in r)
            w = w[:1] if len(set(w)) == 1 else w
            W = '<font color="blue">|</font>'.join(",".join(wo) for wo in w)
            W = "" if W == R else '<font color="red">' + W + "</font> "
            M = ",".join(D[c] for c in m)
            if ns == s:
                loops.append(f'{R} {W}{M}')
            else:
                DOT_DATA.append(f'"{s}" -> "{ns}" [label = <{R} {W}{",".join(D[c] for c in m)}>]')
        if loops:
            DOT_DATA.append(f'"{s}" [label = <<B>{s}</B><BR/>{"<BR/>".join(loops)}>]')
        else:
            DOT_DATA.append(f'"{s}" [label = <<B>{s}</B>>]')
    for s in am.end_states:
        color = ["white", "0.333 0.5 1.0", "0.0 0.25 1.0", "0.1666 0.75 1.0"][
            int(s == am.initial_state) + 2 * int(s in am.end_states)]
        options = f'fillcolor="{color}"'
        DOT_DATA.append(f'"{s}" [style="filled" {options} shape=doubleoctagon];')
    DOT_DATA.append("}")
    dot_proc = subprocess.Popen(['dot', '-Tpdf', '-o' + am.name + '.pdf'], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    outs, errs = dot_proc.communicate(input='\n'.join(DOT_DATA).encode('UTF8'))
    print(*(l for l in outs), end='')
    print(*(l for l in errs), end='')


@cmd(
    ("-i", "--input", "fill the first tape with standard input", None, "store_true"),
    ("-v", "--verbose", "display status information at each iteration", None, "store_true"),
)
def generate(am, input, verbose, **kwargs):
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
    
    while (1)
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
                goto ERROR;
            }}
            
            break;""")
    print(f"""
        default:
            fprintf(stderr, "UNKNOWN STATE '%d'\\n", current);
            return EXIT_FAILURE;
        }}
    }}
    
ERROR:
    fprintf(stderr, "MISSING TRANSITION FROM STATE '%d'\\n", current);
    return EXIT_FAILURE;
}}
""")


def main():
    main_parser = argparse.ArgumentParser()

    subparsers = main_parser.add_subparsers(dest="command", required=True)

    for name, (args, fct) in COMMANDS.items():
        parser = subparsers.add_parser(name, aliases=[name[:3]], help=fct.__doc__)
        parser.set_defaults(func=fct)
        parser.add_argument("filename", help="input filename containing machine description")
        parser.add_argument("-n", "--name", help="name of the machine used", default=None)
        for short, long, help, default, action in args:
            parser.add_argument(short, long, help=help, default=default, action=action)

    args = main_parser.parse_args(argv[1:])

    def get_name(filename, name):
        with open(filename, 'r') as input:
            lm = am_from_string(input.read())
            if name:
                try:
                    return [m for m in lm if m.name == name][-1]
                except IndexError:
                    print(f"no {name} machine found. Names available are :")
                    for m in lm:
                        print(m.name)
                    exit(1)
            elif len(lm) == 1:
                return lm[0]
            else:
                print(f"{len(lm)} machines found. Names available are (use -n name):")
                for m in lm:
                    print(
                        f"{m.name:12} with {m.nb_tapes} tape{'s,' if m.nb_tapes > 1 else ', '} {len(m.transitions):3} states and {len(m.end_states):2} final state{'s.' if len(m.end_states) > 1 else '.'}")
                exit(1)

    m = get_name(args.filename, args.name)
    args.func(m, args=args, **vars(args))


if __name__ == '__main__':
    main()
