#include <stdlib.h>

int main(void)
{
    int *values = malloc(2 * sizeof(*values));
    if (values == NULL) {
        return 1;
    }

    values[2] = 42;
    free(values);
    return 0;
}