#include <stdlib.h>

int main(void)
{
    int *value = malloc(sizeof(*value));
    if (value == NULL) {
        return 1;
    }

    if (*value == 7) {
        *value = 0;
    }

    free(value);
    return 0;
}