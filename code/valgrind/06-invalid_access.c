#include <stdlib.h>

int main(void)
{
    int *values = malloc(2 * sizeof(int));

    values[2] = 42;
    int a = values[2];
    free(values);
    return 0;
}