#include <stdlib.h>

char *g;

int main() 
{
    char *base = malloc(100);
    g = base + 10;   // interior pointer survives to exit
    return 0;
}
