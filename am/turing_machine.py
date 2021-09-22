# coding: utf-8
BLANK = '_'


class Tape:
    """
    Define a set of tapes for a machine
    """

    def __init__(self, N, initial_tape):
        try:
            left, other = initial_tape.split('<')
            head, right = other.split('>')
            if len(head) != 1: raise ValueError
        except:
            if initial_tape:
                left, head, right = "", initial_tape[0], initial_tape[1:]
            else:
                left, head, right = "", BLANK, ""
        self.N, self.initial_tape = N, (left, head, right)
        self.N = N

    @staticmethod
    def _pop(L):
        return L.pop() if L else BLANK

    @staticmethod
    def _append(L, c):
        if L or c != BLANK:
            L.append(c)

    def _reset(self):
        self.stacks = ([c for c in self.initial_tape[0]],) + tuple([] for _ in range(self.N - 1)), \
                      ([c for c in reversed(self.initial_tape[2])],) + tuple([] for _ in range(self.N - 1))
        shift = (len(self.stacks[0][0]) - len(self.stacks[1][0])) // 2
        self.pos = [shift] * self.N
        self.head, self.history = [BLANK] * self.N, []
        self.head[0] = self.initial_tape[1]

    def step(self, writes, moves):
        """
        update the internal state of the tapes with one step
        """
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
        """
        restore the previous state of the tapes before the last step
        """
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
            w, m = self.tape.head, (0,) * self.am.nb_tapes
            self.state, self.result = self.am.undefined_state
        self.tape.step(w, m)
        self.steps += 1

    def back_step(self):
        if self.steps == 0:
            return
        self.tape.backstep()
        self.state = self.history.pop()
        self.steps -= 1