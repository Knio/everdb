#ifndef HASH_H
#define HASH_H

#include <stdint.h>

#ifdef WIN32
#include <windows.h>
#else

#endif

typedef struct {
#ifdef WIN32
    HANDLE h_file;
    HANDLE h_map;
#else
    void* h_file;
    void* h_map;
#endif
    uint64_t size;
} hash_db;


hash_db* hash_open(
    const char* f_name, bool readonly, bool overwrite);

char* hash_get(
    const char* key, uint32_t nkey);

bool hash_put(
    const char* key, uint32_t nkey,
    const char* value, uint32_t nvalue);

#endif
