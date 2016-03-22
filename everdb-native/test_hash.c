#include <stdio.h>
#include "hash.h"

int main() {
    printf("Hello World\n");

    hashdb db = NULL;
    int ret = hash_open(&db, "test.db", 0, 1);
    if (db == NULL) {
        printf("open error %d\n", ret);
        return -1;
    }

    return 0;
}
