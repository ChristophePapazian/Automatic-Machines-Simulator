typedef struct
{
    char* buf;
    size_t size;
    ssize_t position;
} Tape;

Tape tapes[{{am.nb_tapes}}];

char tape_read(size_t tape_num)
{
    const Tape* tape = &tapes[tape_num];

    if (tape->position < 0 || tape->position >= tape->size)
        return BLANK;

    return tape->buf[tape->position];
}

void tape_write(size_t tape_num, char symbol)
{
    Tape* tape = &tapes[tape_num];

    if (tape->position < 0)
    {
        size_t newsize = tape->size - tape->position;
        char* newbuf = malloc(newsize);
        memcpy(newbuf - tape->position, tape->buf, tape->size);
        memset(newbuf, BLANK, -tape->position);
        free(tape->buf);
        tape->buf = newbuf;
        tape->position = 0;
        tape->size = newsize;
    }
    else if (tape->position >= tape->size)
    {
        size_t newsize = tape->position + 1;
        char* newbuf = malloc(newsize);
        memcpy(newbuf, tape->buf, tape->size);
        memset(newbuf + tape->size, BLANK, newsize - tape->size);
        free(tape->buf);
        tape->buf = newbuf;
        tape->size = newsize;
    }

    tape->buf[tape->position] = symbol;
}

void tape_left(size_t tape_num)
{
    tapes[tape_num].position--;
}

void tape_right(size_t tape_num)
{
    tapes[tape_num].position++;
}

void tape_init(size_t tape_num)
{
    tapes[tape_num] = (Tape){ .buf = NULL, .size = 0, .position = 0 };
}

void tape_print(size_t tape_num)
{
    printf("%.*s\n", (int) tapes[tape_num].size, tapes[tape_num].buf);
}