#include <stdlib.h>

int main(void)
{
    int *value = malloc(sizeof(int));

    if (*value == 7) {
        *value = 0;
    }

    free(value);
    return 0;
}