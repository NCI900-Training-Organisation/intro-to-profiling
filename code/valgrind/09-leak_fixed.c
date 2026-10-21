#include <stdlib.h>


int main() 
{
    int *p = malloc(10 * sizeof(int));
    p[0] = 42;
    free(p);
    return 0;   
}