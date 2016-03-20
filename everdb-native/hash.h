#include <stdint.h>

#ifdef WIN32

#include <windows.h>

typedef struct {
    HANDLE h_file;
    HANDLE h_map;
    uint64_t size;
} hash_db;

#else

typedef struct {
    void* h_file;
    void* h_map;
    uint64_t size;
} hash_db;

#endif




hash_db* hash_open(
    const char* f_name, bool readonly, bool overwrite);

char* hash_get(
    const char* key, uint32_t nkey);

bool hash_put(
    const char* key, uint32_t nkey,
    const char* value, uint32_t nvalue);
