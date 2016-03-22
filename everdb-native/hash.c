#include "hash.h"
#include <malloc.h>
#include <stdio.h>

#ifdef _WIN32
#include <windows.h>
#include <io.h>
#else
#include <sys/mman.h>
#endif

struct hashdb_s {
#ifdef _WIN32
    HANDLE h_file;
    HANDLE h_map;
#else
    FILE* h_file;
    void* h_map;
#endif
    uint64_t size;
};


int hash_open(hashdb *db, const char* fname, int readonly, int overwrite) {
    *db = NULL;
    int ret = 0;

    *db = (hashdb) malloc(sizeof(**db));
    memset(*db, 0, sizeof(**db));

    if (*db == NULL) {
        // allocate error
        ret = -2;
        goto err;
    }

#ifdef _WIN32
    if (readonly && overwrite) {
        ret = -4;
        goto err;
    }
    (*db)->h_file = CreateFileA(fname,
        readonly ? GENERIC_READ : (GENERIC_READ | GENERIC_WRITE),
        0,
        NULL,
        overwrite ? CREATE_ALWAYS : OPEN_ALWAYS,
        0,
        NULL
    );
    if ((*db)->h_file == NULL) {
        ret = -1;
        goto err;
    }

    LARGE_INTEGER f_size;
    if (!GetFileSizeEx((*db)->h_file, &f_size)) {
        ret = -3;
        goto err;
    }
    (*db)->size = f_size.QuadPart;
#else
    //linux here
#endif

    if ((*db)->size == 0) {
        // new or overwritten file
        hash_init(*db);
    }
    else {
        // existing file
        hash_check(*db);
    }

    return ret;

    err:
    if((*db)->h_file != NULL) {
#ifdef _WIN32
        CloseHandle((*db)->h_file);
#endif
    }
    if(*db != NULL) {
        free(*db);
    }
    return ret;
}


int hash_check(const hashdb db) {
    return 0;
}

int hash_init(hashdb db) {
    return 0;
}


char* hash_get(const hashdb db, const char* key, uint32_t nkey) {
    return NULL;
}

int hash_put(hashdb db, const char* key, uint32_t nkey, const char* value,
             uint32_t nvalue) {
    return 0;
}

