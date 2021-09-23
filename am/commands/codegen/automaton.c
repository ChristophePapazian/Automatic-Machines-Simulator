#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const char BLANK = '{{BLANK}}';

{% if linked %}
{% include "list_linked.c" %}
{% else %}
{% include "list_linear.c" %}
{% endif %}

typedef int state_t;

#define BUF_SIZE 256
#define MIN(a,b) (((a)<(b))?(a):(b))
#define MAX(a,b) (((a)>(b))?(a):(b))

void display(state_t current)
{
    printf("Current state : %d\n", current);
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
    size_t input_size = 0;
    size_t current_size = BUF_SIZE;
    char* input_buf = malloc(current_size);
    memset(input_buf, BLANK, current_size);
    size_t read;
    while ((read = fread(input_buf + input_size, 1, current_size - input_size, stdin)) > 0)
    {
        input_size += read;
        if (current_size - input_size < 16)
        {
            input_buf = realloc(input_buf, current_size += BUF_SIZE);
        }
    }

    input_buf = realloc(input_buf, input_size);

    tapes[0] = (Tape){ .buf = input_buf, .size = input_size, .position = 0 };
    {% endif %}

    state_t current = {{all_states[am.initial_state][0]}};

    for (size_t step = 0; ; step++)
    {
        {% if verbose %}
        display(current);
        {% endif %}

        char tape_values[] = { {% for tape in range(am.nb_tapes) %} tape_read({{tape}}), {% endfor %} };
        switch (current)
        {

    {% for state, (number, message) in end_states.items() %}
        case {{number}}: // {{state}}
            display(current);
            SHOW_STEP();
            fprintf(stderr, "END STATE '%s': %s\n", {{json.dumps(state)}}, {{json.dumps(message)}});
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
                SHOW_STEP();
                goto ERROR;
            }

            break;
    {% endfor %}

        default:
            SHOW_STEP();
            fprintf(stderr, "UNKNOWN STATE '%d'\n", current);
            return EXIT_FAILURE;
        }
    }

ERROR:
    fprintf(stderr, "MISSING TRANSITION FROM STATE '%d'\n", current);
    return EXIT_FAILURE;
}