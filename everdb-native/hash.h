#ifndef HASH_H
#define HASH_H

#include <stdint.h>

#ifdef _WIN32
#include <windows.h>
#else

#endif

/**
 * Hashdb object
 */
typedef struct hashdb_s* hashdb;


/**
 * Open or create a hashdb file
 */
hashdb hash_open(const char* f_name, int readonly, int overwrite);

/**
 * lookup a key
 * @return value of key
 */
char* hash_get(const hashdb db, const char* key, uint32_t nkey);

/**
 * Insert or overwrite a key
 */
int hash_put(hashdb db, const char* key, uint32_t nkey, const char* value,
             uint32_t nvalue);

/**
 * Initialize a new empty db
 */
int hash_init(hashdb db);

/**
 * Check header / checksums / etc
 */
int hash_check(const hashdb db);

#endif
