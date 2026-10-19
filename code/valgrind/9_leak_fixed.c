#include <stdlib.h>

int main(void)
{
    int *values = malloc(10 * sizeof(*values));
    if (values == NULL) {
        return 1;
    }

    values[0] = 42;
    free(values);
    return 0;
}