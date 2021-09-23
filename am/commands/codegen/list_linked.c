struct tape_s;

typedef struct tape_s
{
    char symbol;
    struct tape_s* left;
    struct tape_s* right;
} tape_t, *Tape;

Tape tapes[{{am.nb_tapes}}];

char tape_read(size_t tape_num)
{
    return tapes[tape_num]->symbol;
}

void tape_write(size_t tape_num, char symbol)
{
    tapes[tape_num]->symbol = symbol;
}

void tape_left(size_t tape_num)
{
    Tape* tape = &tapes[tape_num];

    if ((*tape)->left == NULL)
    {
        *((*tape)->left = malloc(sizeof(Tape))) = (tape_t){ .symbol = BLANK, .left = NULL, .right = *tape };
    }

    *tape = (*tape)->left;
}

void tape_right(size_t tape_num)
{
    Tape* tape = &tapes[tape_num];

    if ((*tape)->right == NULL)
    {
        *((*tape)->right = malloc(sizeof(Tape))) = (tape_t){ .symbol = BLANK, .left = *tape, .right = NULL };
    }

    *tape = (*tape)->right;
}

void tape_init(size_t tape_num)
{
    *(tapes[tape_num] = malloc(sizeof(Tape))) = (tape_t){ .symbol = BLANK, .left = NULL, .right = NULL };
}

void tape_print(size_t tape_num)
{
    Tape tape = tapes[tape_num];
    while (tape->left != NULL)
        tape = tape->left;
    do
    {
        putchar(tape->symbol);
    } while ((tape = tape->right) != NULL);

    putchar('\n');
}