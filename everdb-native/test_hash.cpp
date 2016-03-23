#define CATCH_CONFIG_MAIN
#include "lib/catch.hpp"

#include "hash.h"


TEST_CASE() {

  hash db;

  // open new db + overwrite
  REQUIRE(hash_open(&db, "test.db", 0, 1) == 0);
  REQUIRE(db.size == 4096);

  // hacks
  memcpy(db.data, "test 123", 8);

  // save it
  hash_close(&db);

  // open it again and see if data still there
  REQUIRE(hash_open(&db, "test.db", 0, 0) == 0);
  REQUIRE(memcmp(db.data, "test 123", 8) == 0);

}
