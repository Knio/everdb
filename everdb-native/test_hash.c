#include <stdio.h>
#include "hash.h"

int main() {
    printf("Hello World\n");

    hashdb db = hash_open("test.db", FALSE, TRUE);
    if (db == NULL) {
        printf("open error\n");
        return -1;
    }

    return 0;
}
