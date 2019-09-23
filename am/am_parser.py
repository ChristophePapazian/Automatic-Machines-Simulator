import ply.yacc as yacc
import sys

from am.am_lex import tokens


def update_cst(d1, d2, s):
    if isinstance(d2, dict):
        for r in d2:
            if r in d1:
                raise ValueError('Transition already defined state @%s read \'%s' % (s, r))
            d1[r] = d2[r]
    elif isinstance(d2, list):
        for r, t in d2:
            if r in d1:
                raise ValueError(f'Transition already defined state @{s} read {r} : {t}')
            d1[r] = t


class AM:
    __slots__ = ('transitions', 'initial_state', 'end_states', 'undefined_state', 'nb_tapes', 'name')

    def __repr__(self):
        return f'{self.name} {self.nb_tapes} >{self.initial_state} {self.end_states} {self.undefined_state} {len(self.transitions)}/{sum(len(i) for i in self.transitions.values())}'

    def set_transitions(self, tr):
        self.transitions = {}
        for s in tr:
            self.transitions[s] = {}
            for t in tr[s]:
                if len(t) != self.nb_tapes:
                    raise ValueError(f'inconsistent number of tapes in {self.name} {s} : got {len(t)}, expecting {self.nb_tapes}')
                sl = {len(l) for s in (t, tr[s][t][0]) for l in s}
                sl.discard(1)
                if len(sl) > 1:
                    raise ValueError(f'inconsistent number of options in {self.name} {sl}')
                if not sl:
                    mv, ns = tr[s][t][1:]
                    if ns is None: ns = s
                    update_cst(self.transitions[s], {tuple(r[0] for r in t): ((tuple(r[0] for r in tr[s][t][0])), mv, ns)}, s)
                else:
                    mv, ns = tr[s][t][1:]
                    if ns is None: ns = s
                    for i in range(sl.pop()):
                        update_cst(self.transitions[s], {tuple(r[i if len(r) > 1 else 0] for r in t): ((tuple(r[i if len(r) > 1 else 0] for r in tr[s][t][0])), mv, ns)}, s)


def p_all(p):
    '''
    all : am
        | all am
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]
        p[0].append(p[2])


def p_am(p):
    '''
    am : name specif trans
    '''
    res = AM()
    res.initial_state = p[2][0]
    res.end_states = p[2][1]
    res.undefined_state = p[2][2]
    res.nb_tapes = p[1][1]
    res.name = p[1][0]
    res.set_transitions(p[3])

    p[0] = res


def p_name(p):
    '''
    name : NEW STRING INT
    '''
    p[0] = p[2:]


def p_specif(p):
    '''
    specif : start
           | start ends
           | start ends s_error
    '''
    p[0] = p[1:]
    if len(p[0]) < 2:
        p[0].append(())
    if len(p[0]) < 3:
        p[0].append(('ERROR', 'ERROR'))
    p[0] = tuple(p[0])


def p_start(p):
    '''
    start : START STATE
    '''
    p[0] = p[2]


def p_ends(p):
    '''
    ends : end
         | ends end
    '''
    if len(p) == 2:
        p[0] = {p[1][0]: p[1][1]}
    else:
        p[0] = p[1]
        if p[2][0] in p[0]:
            raise ValueError(f'multiple end results for state {p[2][0]}')
        p[0][p[2][0]] = p[2][1]


def p_end(p):
    '''
    end : END STATE STRING
    s_error : UNDEFINED STATE STRING
    '''
    p[0] = p[2], p[3]


def p_am_1(p):
    '''
    trans : state_tr
    '''
    p[0] = {p[1][0]: p[1][1]}


def p_am_2(p):
    '''
    trans : trans state_tr
    '''
    p[0] = p[1]
    if p[2][0] in p[0]:
        update_cst(p[0][p[2][0]], p[2][1], p[2][0])
    else:
        p[0][p[2][0]] = p[2][1]


def p_state(p):
    '''
    state_tr : full_transition transition_list
    '''
    update_cst(p[1][1], p[2], p[1][0])
    p[0] = p[1]


def p_full_transition(p):
    '''
    full_transition : FROM STATE transition
    '''
    p[0] = p[2], {p[3][0]: p[3][1]}


def p_transition(p):
    '''
    transition : reads writes moves STATE
    transition : reads writes moves
    '''
    if not p[2]:
        p[2] = p[1]
    if len(set(len(i) for i in p[1:4])) > 1:
        raise ValueError('Inconsistent numbers of heads in transition')
    p[0] = tuple(p[1]), (tuple(p[2]), tuple(p[3]), p[4] if len(p) > 4 else None)


def p_transition_list(p):
    '''
    transition_list : transition_list transition
                    | empty
    '''
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = p[1]
        p[0].append(p[2])


def p_empty(p):
    'empty :'
    pass


def p_reads(p):
    '''
    reads : letters
          | reads COMMA letters
    moves : MOVE
          | moves COMMA MOVE
    letters : LETTER
          | letters PIPE LETTER
    '''
    if len(p) == 2:
        p[0] = (p[1],)
    else:
        p[0] = p[1] + (p[3],)


def p_writes(p):
    '''
    writes : reads
           | empty
    '''
    p[0] = p[1] or []


def p_error(p):
    if p is None:
        print("Syntax error : unexpected end of file", file=sys.stderr)
    else:
        print(f"Syntax error in input on token {p.type} {p.value} on line {p.lineno} at pos {p.lexpos}", file=sys.stderr)
        if p.type == p.value == 'END':
            print("Maybe you forgot the START statement before END ?", file=sys.stderr)
        sys.exit(-1)


parser = yacc.yacc()


def am_from_string(s):
    lm = parser.parse(s)
    for m in lm:
        for e in m.end_states:
            if e in m.transitions:
                raise ValueError(f"end state {e} with transitions in {m.name}")
    return lm
