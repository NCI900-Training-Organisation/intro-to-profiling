#include <stdlib.h>

int *global;

int main() 
{
    global = malloc(100);
    return 0;          // memory still reachable via global
}
