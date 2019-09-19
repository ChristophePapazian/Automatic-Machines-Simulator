# V1.2 2019/09/19 Christophe Papazian

import argparse
import curses
from time import sleep

class UI_Curses:
    def __init__(self, sim):
        self.sim = sim
        curses.wrapper(self.term)

    def yx(self, p, t):
        p += self.COLS // 2
        return (p // self.COLS) * (self.sim.am.nb_tapes + 1) + t + self.LINES // 2, p % self.COLS

    def print_tapes(self):
        for p, l, h, r, t in zip(self.sim.tape.pos, self.sim.tape.stacks[0], self.sim.tape.head, self.sim.tape.stacks[1], range(self.sim.am.nb_tapes)):
            k = p - 1
            for c in reversed(l):
                try:
                    self.stdscr.addstr(*self.yx(k, t), c, curses.A_NORMAL | self.color_pair(t))
                except curses.error:
                    pass
                k -= 1
            try:
                self.stdscr.addstr(*self.yx(p, t), h, curses.A_REVERSE | self.color_pair(t))
            except curses.error:
                pass
            k = p + 1
            for c in reversed(r):
                try:
                    self.stdscr.addstr(*self.yx(k, t), c, curses.A_NORMAL | self.color_pair(t))
                except curses.error:
                    pass
                k += 1

    def print_state(self):
        self.stdscr.addstr(0, 0, self.sim.state, curses.A_BOLD)
        self.stdscr.addstr(0, self.COLS - len(str(self.sim.steps)), str(self.sim.steps), curses.A_BOLD)
        if self.sim.result is not None:
            self.stdscr.addstr(1, 0, self.sim.result, curses.A_REVERSE)

    def term(self, stdscr):
        self.stdscr = stdscr
        self.can_use_color = curses.can_change_color()
        if not self.can_use_color:
            self.color_pair = lambda t: 0
        else:
            self.color_pair = curses.color_pair
        self.LINES, self.COLS = stdscr.getmaxyx()
        if self.can_use_color:
            curses.start_color()
            curses.use_default_colors()
            try:
                for i, c in enumerate([curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_YELLOW, curses.COLOR_GREEN, curses.COLOR_MAGENTA, curses.COLOR_RED, curses.COLOR_BLUE]):
                    curses.init_pair(i, c, 0)
            except curses.error:
                self.can_use_color = False
                self.color_pair = lambda t: 0
        curses.curs_set(0)
        stdscr.nodelay(True)
        delay, c, back = 0, '', False
        while True:
            if delay >= 0 or self.sim.result:
                stdscr.clear()
                self.print_tapes()
                self.print_state()
                if delay == 0:
                    stdscr.addstr(1, self.COLS - 5, "PAUSE", curses.A_REVERSE | curses.A_BOLD | self.color_pair(5))
                if self.sim.result:
                    stdscr.addstr(
                        self.LINES - 1, 0, 'SIMULATION COMPLETED. Press b to go backward, r to restart, any to quit'[:self.COLS - 1])
                stdscr.refresh()
            stdscr.nodelay(delay != 0)
            try:
                c = stdscr.getkey()
            except curses.error:
                c = None
            if c:
                if c == '+':
                    delay = 0.25 if delay == 0 else delay * 0.5
                elif c == '-':
                    delay = 0 if delay >= 2 else delay * 2
                elif c == 'p':
                    delay = 0
                elif c == 'q':
                    return
                elif c == 'e':
                    delay = -1
                elif c == 'b':
                    delay = 0
                    back = True
                elif c == 'r':
                    delay = 0
                    self.sim.reset()
                    continue
                elif c == 'KEY_RESIZE':
                    self.LINES, self.COLS = stdscr.getmaxyx()
                    continue
            if delay > 0:
                sleep(delay)
            if back:
                self.sim.back_step()
                back = False
                self.sim.result = None
            else:
                if self.sim.result is not None:
                    if delay == 0:
                        return
                    else:
                        delay = 0
                self.sim.step()

