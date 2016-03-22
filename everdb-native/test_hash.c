#include <stdio.h>
#include "hash.h"

int main() {
  printf("Testing..\n");

  hash db;

  // open new db + overwrite
  int ret = hash_open(&db, "test.db", 0, 1);
  if (ret) {
    printf("open error %d\n", ret);
    return -1;
  }

  // hacks
  memcpy(db.data, "test 123", 8);

  // save it
  hash_close(&db);

  // open it again and see if data still there
  ret = hash_open(&db, "test.db", 0, 0);
  if (ret) {
    printf("open error %d\n", ret);
    return -1;
  }

  if (memcmp(db.data, "test 123", 8)) {
    printf("Data error: %*s", 8, (char*)db.data);
  }

  printf("Hello World\n");
  return 0;
}
