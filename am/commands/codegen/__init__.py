# coding: utf-8
import json
import os
from pathlib import Path

from am.commands import cmd
from am.turing_machine import BLANK


@cmd(
    ("-i", "--input", "fill the first tape with standard input", None, "store_true"),
    ("-v", "--verbose", "display status information at each iteration", None, "store_true"),
    ("-l", "--linked", "use linked list instead of linear buffer allocation (for tapes)", False, "store_true"),
)
def codegen(am, input, verbose, linked, **kwargs):
    """
    Generates a C implementation of an automatic machine.
    """
    states = {state: (i, transitions) for i, (state, transitions) in enumerate(am.transitions.items())}
    end_states = {state: (-1 - i, message) for i, (state, message) in enumerate(am.end_states.items())}
    all_states = {**states, **end_states}

    from jinja2 import Environment, PackageLoader, select_autoescape
    env = Environment(
        loader=PackageLoader("am.commands", "codegen"),
        autoescape=select_autoescape()
    )
    env.globals.update(globals())
    tm = env.get_template("automaton.c")
    print(tm.render(**locals(), zip=zip))

