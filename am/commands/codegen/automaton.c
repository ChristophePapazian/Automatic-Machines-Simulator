#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const char BLANK = '{{BLANK}}';

{% if linear %}
{% include "list_linear.c" %}
{% else %}
{% include "list_linked.c" %}
{% endif %}

typedef int state_t;

#define MIN(a,b) (((a)<(b))?(a):(b))
#define MAX(a,b) (((a)>(b))?(a):(b))

void display(size_t step, state_t current)
{
    printf("Step %zu, current state : %d\n", step, current);
    for (size_t num = 0; num < {{am.nb_tapes}}; num++)
    {
        printf("Tape %2zu : ", num);
        tape_print(num);
    }
    fflush(stdout);
}

#define SHOW_STEP() fprintf(stderr, "Step count: %zu\n", step)

int main()
{
    for (int i = 0; i < {{am.nb_tapes}}; i++)
    {
        tape_init(i);
    }

    {% if input %}
    tape_read_stdin();
    {% endif %}

    state_t current = {{all_states[am.initial_state][0]}};

    for (size_t step = 0; ; step++)
    {
        {% if verbose %}
        display(step, current);
        {% endif %}

        char tape_values[] = { {% for tape in range(am.nb_tapes) %} tape_read({{tape}}), {% endfor %} };
        switch (current)
        {

    {% for state, (number, message) in end_states.items() %}
        case {{number}}: // {{state}}
            fprintf(stderr, "END STATE '%s': %s\n", {{json.dumps(state)}}, {{json.dumps(message)}});
            display(step, current);
            return EXIT_SUCCESS;
    {% endfor %}

    {% for state, (number, transitions) in states.items() %}
        case {{number}}: // {{state}}
        {% for read, (write, moves, next_state) in transitions.items() %}
            {{"else " if loop.index0 != 0 else ""}}if (1 {% for value in read %} && tape_values[{{loop.index0}}] == '{{value}}' {% endfor %})
            {
                {% for value in write %} tape_write({{loop.index0}}, '{{value}}'); {% endfor %}
                {% for delta in moves %} {% if delta == 1 %} tape_right({{loop.index0}}); {% elif delta == -1 %} tape_left({{loop.index0}}); {% endif %} {% endfor %}
                current = {{all_states[next_state][0]}};
            }
        {% endfor %}
            else
            {
                fprintf(stderr, "MISSING TRANSITION FROM STATE '%d'\n", current);
                display(step, current);
                return EXIT_FAILURE;
            }

            break;
    {% endfor %}

        default:
            fprintf(stderr, "UNKNOWN STATE '%d'\n", current);
            display(step, current);
            return EXIT_FAILURE;
        }
    }
}