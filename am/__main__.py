# V1.1 2018/10/30 Christophe Papazian

import argparse
from collections import defaultdict
from am.am_parser import am_from_string
from am.am_curses import UI_Curses
import sys

BLANK = '_'


class Tape:
    def __init__(self, N, initial_tape):
        try:
            left, other = initial_tape.split('<')
            head, right = other.split('>')
            if len(head)!= 1 : raise ValueError
        except:
            print("Initial tape error.")
            sys.exit(37)
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="input filename containing machine description")
    parser.add_argument("-t", "--tape", help="initial tape. First position inside angle brackets <.>", default="<_>")
    parser.add_argument("-n", "--name", help="name of the machine used", default=None)
    parser.add_argument("-r", "--result-only", help="no simulation, result only", action="store_true")
    parser.add_argument("-s", "--statistics", help="print detailed statistics", action="store_true")
    args = parser.parse_args()
    with open(args.filename, 'r') as input:
        lm = am_from_string(input.read())
        if args.name:
            try:
                m = [m for m in lm if m.name == args.name][-1]
            except IndexError:
                print(f"no {args.name} machine found. Names available are :")
                for m in lm:
                    print(m.name)
                return
        elif len(lm)==1:
            m = lm[0]
        else:
                print(f"{len(lm)} machines found. Names available are (use -n name):")
                for m in lm:
                    print(f"{m.name:12} with {m.nb_tapes} tape{'s,' if m.nb_tapes>1 else ', '} {len(m.transitions):3} states and {len(m.end_states):2} final state{'s.' if len(m.end_states)>1 else '.'}")
                return

    simulation(m, args.tape, result_only=args.result_only, statistics=args.statistics)


if __name__ == '__main__':
    main()
