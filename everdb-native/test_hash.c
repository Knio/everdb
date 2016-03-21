#include <stdio.h>
#include "hash.h"

int main() {
    printf("Hello World\n");

    hashdb db = NULL;
    int ret = hash_open(&db, "test.db", HASH_OW);
    if (db == NULL) {
        printf("open error %d\n", ret);
        return -1;
    }

    return 0;
}
