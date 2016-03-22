#ifndef HASH_H
#define HASH_H

#include <stdint.h>

#ifdef _WIN32
#include <windows.h>
#endif


#define BLOCK_BITS (12) // 4096
#define BLOCK_SIZE (1 << BLOCK_BITS)
#define BLOCK_MASK (BLOCK_SIZE - 1)


/**
 * Hashdb object
 */
typedef struct {
    int readonly;
#ifdef _WIN32
    HANDLE h_file;
    HANDLE h_mapping;
#else
    int h_file;
    void* h_map;
#endif
    void* data;
    uint64_t size;
} hash;


/**
 * Open or create a hashdb file
 * The database or null is returned in the hashdb param
 * @return 0 on success, -1 on open error, other values on other errors
 */
int hash_open(hash *db, const char* f_name,
        int readonly,
        int overwrite);


void hash_close(hash *db);

/**
 * lookup a key
 * @return value of key
 */
char* hash_get(const hash *db,
        const char* key, uint32_t nkey);

/**
 * Insert or overwrite a key
 */
int hash_put(hash *db,
        const char* key, uint32_t nkey,
        const char* value, uint32_t nvalue);

/**
 * Initialize a new empty db
 */
int hash_init(hash *db);

/**
 * Check header / checksums / etc
 */
int hash_check(const hash *db);

#endif
