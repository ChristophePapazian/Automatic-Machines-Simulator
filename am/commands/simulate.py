# coding: utf-8
from collections import defaultdict

from am.commands import cmd
from am.am_curses import UI_Curses
from am.turing_machine import Simulation


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