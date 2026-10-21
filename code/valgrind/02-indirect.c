#include <stdlib.h>

struct S {
    int *data;
};

int main() 
{
    struct S *s = malloc(sizeof(struct S));
    s->data = malloc(10 * sizeof(int));
    return 0; // s leaked s->data is indirectly lost
}
