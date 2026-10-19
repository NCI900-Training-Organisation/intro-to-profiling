#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void use_after_free(void)
{
    int *value = malloc(sizeof(*value));
    if (value == NULL) {
        exit(1);
    }
    *value = 42;
    free(value);
    printf("value: %d\n", *value);
}

static void double_free(void)
{
    int *value = malloc(sizeof(*value));
    if (value == NULL) {
        exit(1);
    }
    free(value);
    free(value);
}

static void invalid_free(void)
{
    int value = 42;
    free(&value);
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "Usage: %s use-after-free|double-free|invalid-free\n", argv[0]);
        return 2;
    }

    if (strcmp(argv[1], "use-after-free") == 0) {
        use_after_free();
    } else if (strcmp(argv[1], "double-free") == 0) {
        double_free();
    } else if (strcmp(argv[1], "invalid-free") == 0) {
        invalid_free();
    } else {
        fprintf(stderr, "Unknown scenario: %s\n", argv[1]);
        return 2;
    }

    return 0;
}