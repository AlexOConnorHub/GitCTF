#include <stdio.h>
#include <stdlib.h>

#define BUF_SIZE 10

int main()
{
    char buf[BUF_SIZE];
    fgets(buf, BUF_SIZE, stdin);
    puts(buf);
    fflush(stdout);
    if(!strcmp(buf, "bug"))
    {
        system("/bin/bash");
    }
    return 0;
}
