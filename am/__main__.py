# V1.2 2019/09/19 Christophe Papazian

import argparse
from collections import defaultdict
from am.am_parser import am_from_string
from am.am_curses import UI_Curses
from sys import argv, exit, stdout
import subprocess

BLANK = '_'


class Tape:
    '''
    Define a set of tapes for a machine
    '''
    def __init__(self, N, initial_tape):
        try:
            left, other = initial_tape.split('<')
            head, right = other.split('>')
            if len(head)!= 1 : raise ValueError
        except:
            if initial_tape:
                left, head, right = "", initial_tape[0], initial_tape[1:]
            else :
                left, head, right = "", BLANK, ""
        self.N, self.initial_tape = N, (left,head,right)
        self.N = N

    @staticmethod
    def _pop(L): return L.pop() if L else BLANK

    @staticmethod
    def _append(L, c):
        if L or c != BLANK:
            L.append(c)

    def _reset(self):
        self.stacks = ([c for c in self.initial_tape[0]],) + tuple([] for _ in range(self.N - 1)), \
            ([c for c in reversed(self.initial_tape[2])],) + tuple([] for _ in range(self.N - 1))
        shift = (len(self.stacks[0][0])-len(self.stacks[1][0]))//2
        self.pos = [shift]*self.N
        self.head, self.history = [BLANK]*self.N, []
        self.head[0]=self.initial_tape[1]

    def step(self, writes, moves):
        '''
        update the internal state of the tapes with one step
        '''
        self.history.append((tuple(self.head), moves))
        for i in range(self.N):
            if moves[i]:
                self.head[i] = Tape._pop(self.stacks[moves[i] > 0][i])
                Tape._append(self.stacks[moves[i] < 0][i], writes[i])
            else:
                self.head[i] = writes[i]
        for i in range(self.N):
            self.pos[i] += moves[i]

    def backstep(self):
        '''
        restore the previous state of the tapes before the last step
        '''
        head, moves = self.history.pop()
        for i in range(self.N):
            if moves[i]:
                Tape._pop(self.stacks[moves[i] < 0][i])
                Tape._append(self.stacks[moves[i] > 0][i], self.head[i])
            self.head[i] = head[i]
        for i in range(self.N):
            self.pos[i] -= moves[i]


class Simulation:
    def __init__(self, am, tape):
        self.tape, self.am = Tape(am.nb_tapes, tape), am
        self.reset()

    def reset(self):
        self.tape._reset()
        self.state, self.steps, self.result, self.history = self.am.initial_state, 0, None, []

    def step(self):
        if self.result is not None:
            return
        self.history.append(self.state)
        try:
            w, m, self.state = self.am.transitions[self.state][tuple(self.tape.head)]
            self.result = self.am.end_states[self.state] if self.state in self.am.end_states else None
        except KeyError:
            w, m = self.tape.head, (0,)*self.am.nb_tapes
            self.state, self.result = self.am.undefined_state
        self.tape.step(w, m)
        self.steps += 1

    def back_step(self):
        if self.steps == 0:
            return
        self.tape.backstep()
        self.state = self.history.pop()
        self.steps -= 1


def simulation(am, tape,  result_only=False, statistics=False):
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


def draw(am, name, file=None):
    '''
    Create a pdf file from an automatic machine. 
    Requirement : the dot program from GraphViz
    '''
    DOT_DATA = []
    D={-1:"L", 0:"S", 1:"R"}
    if file is None : file=stdout
    DOT_DATA.append("digraph {")
    DOT_DATA.append(" graph [mclimit = 100 rankdir = LR]")
    # print(' edge [lblstyle="sloped"];') 
    DOT_DATA.append(' QI0123456789 [shape=point]')
    DOT_DATA.append(f' QI0123456789 -> {am.initial_state}')
    for s in am.transitions:
        loops = []
        T = defaultdict(list)
        color = ["white", "0.333 0.5 1.0", "0.0 0.25 1.0", "0.1666 0.75 1.0"][int(s==am.initial_state)+2*int(s in am.end_states)]
        options = f'fillcolor="{color}"'
        DOT_DATA.append(f'"{s}" [style="filled" {options}]')
        for r in am.transitions[s]:
            w, m, ns = am.transitions[s][r]
            T[(m,ns)].append((r,w))
        for m,ns in T:
            r,w = zip(*T[(m,ns)])
            R = '<font color="blue">|</font>'.join(",".join(ro) for ro in r)
            w = w[:1] if len(set(w))==1 else w
            W = '<font color="blue">|</font>'.join(",".join(wo) for wo in w)
            W = "" if W==R else '<font color="red">'+W+"</font> "
            M = ",".join(D[c] for c in m)
            if ns == s :
                loops.append(f'{R} {W}{M}')
            else :
                DOT_DATA.append(f'"{s}" -> "{ns}" [label = <{R} {W}{",".join(D[c] for c in m)}>]')
        if loops:
            DOT_DATA.append(f'"{s}" [label = <<B>{s}</B><BR/>{"<BR/>".join(loops)}>]')
        else:
            DOT_DATA.append(f'"{s}" [label = <<B>{s}</B>>]')
    for s in am.end_states:
        color = ["white", "0.333 0.5 1.0", "0.0 0.25 1.0", "0.1666 0.75 1.0"][int(s==am.initial_state)+2*int(s in am.end_states)]
        options = f'fillcolor="{color}"'
        DOT_DATA.append(f'"{s}" [style="filled" {options} shape=doubleoctagon];')
    DOT_DATA.append("}")
    dot_proc = subprocess.Popen(['dot', '-Tpdf', '-o'+name+'.pdf'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    outs, errs = dot_proc.communicate(input='\n'.join(DOT_DATA).encode('UTF8'))
    print(*(l for l in outs), end='')
    print(*(l for l in errs), end='')

def main():
    main_parser = argparse.ArgumentParser()
    main_parser.add_argument("command", help="simulate|draw")

    args = main_parser.parse_args(argv[1:2])

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
            elif len(lm)==1:
                return lm[0]
            else:
                print(f"{len(lm)} machines found. Names available are (use -n name):")
                for m in lm:
                    print(f"{m.name:12} with {m.nb_tapes} tape{'s,' if m.nb_tapes>1 else ', '} {len(m.transitions):3} states and {len(m.end_states):2} final state{'s.' if len(m.end_states)>1 else '.'}")
                exit(1)

    ### SIMULATION
    if args.command[:3] == "sim":
        parser = argparse.ArgumentParser()
        parser.add_argument("filename", help="input filename containing machine description")
        parser.add_argument("-t", "--tape", help="initial tape. First position inside angle brackets <.>", default="<_>")
        parser.add_argument("-n", "--name", help="name of the machine used", default=None)
        parser.add_argument("-r", "--result-only", help="no simulation, result only", action="store_true")
        parser.add_argument("-s", "--statistics", help="print detailed statistics", action="store_true")
        args = parser.parse_args(argv[2:])
        m = get_name(args.filename, args.name)
        simulation(m, args.tape, result_only=args.result_only, statistics=args.statistics)
    ### DRAW
    elif args.command[:3] == "dra":
        parser = argparse.ArgumentParser()
        parser.add_argument("filename", help="input filename containing machine description")
        parser.add_argument("-n", "--name", help="name of the machine used", default=None)
        args = parser.parse_args(argv[2:])
        m = get_name(args.filename, args.name)
        draw(m, args.name)
    else:
        print("unknown command {args.command}.")

if __name__ == '__main__':
    main()
