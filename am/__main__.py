# V1.2 2019/09/19 Christophe Papazian

import argparse
import subprocess
from collections import defaultdict
from sys import argv, exit, stdout

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
