#include <stdlib.h>

/* -------- still reachable -------- */
int *global_reachable;

/* -------- possibly lost -------- */
char *global_interior;

struct Node {
    int *data;
};

int main(void) 
{

    /* Definitely lost */
    int *def = malloc(10 * sizeof(int));
    (void)def;

    /* Indirectly lost */
    struct Node *n = malloc(sizeof(struct Node));
    n->data = malloc(20 * sizeof(int));
    (void)n;

    /* Possibly lost */
    char *base = malloc(100);
    global_interior = base + 10;   // interior pointer survives
    (void)global_interior;

    /* Still reachable */
    global_reachable = malloc(50 * sizeof(int));

    return 0;
}
