
#include <cstdio>
#include "hash.h"

int main() {
    printf("Hello World\n");

    hash_db *db = hash_open("test.db", false, true);
    if (db == NULL) {
        printf("open error\n");
        return -1;
    }

    return 0;
}
