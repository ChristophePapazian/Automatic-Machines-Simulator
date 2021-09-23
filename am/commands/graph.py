# coding: utf-8
import subprocess
from collections import defaultdict

from am.commands import cmd


def get_dot(am):
    DOT_DATA = []
    D = {-1: "L", 0: "S", 1: "R"}
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
    return "\n".join(DOT_DATA)


@cmd()
def graph(am, **kwargs):
    """
    Generates a dot graph from an automatic machine.
    """
    print(get_dot(am))


@cmd()
def draw(am, **kwargs):
    """
    Create a pdf file from an automatic machine.
    Requirement : the dot program from GraphViz
    """
    DOT_DATA = get_dot(am)
    dot_proc = subprocess.Popen(['dot', '-Tpdf', '-o' + am.name + '.pdf'], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    outs, errs = dot_proc.communicate(input=DOT_DATA.encode('UTF8'))
    print(*(l for l in outs), end='')
    print(*(l for l in errs), end='')
