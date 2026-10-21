#include <stdio.h>
#include <stdlib.h>

#define ELEMENT_COUNT (256 * 1024)
#define ITERATION_COUNT 12

static volatile unsigned long checksum;

static void update_values(int *values, size_t count, int iteration)
{
    for (size_t index = 0; index < count; ++index) {
        values[index] = (int)((values[index] + index + (size_t)iteration) % 997);
        checksum += (unsigned long)values[index];
    }
}

int main(void)
{
    int *values = malloc(ELEMENT_COUNT * sizeof(*values));
    if (values == NULL) {
        perror("malloc");
        return 1;
    }

    for (size_t index = 0; index < ELEMENT_COUNT; ++index) {
        values[index] = (int)(index % 97);
    }

    for (int iteration = 0; iteration < ITERATION_COUNT; ++iteration) {
        update_values(values, ELEMENT_COUNT, iteration);
    }

    printf("checksum: %lu\n", checksum);
    free(values);
    return 0;
}