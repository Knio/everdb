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
    FILE* h_file;
#ifdef _WIN32
    HANDLE h_map;
#else
    void* h_map;
#endif
    uint64_t size;
};


int hash_open(hashdb *db, const char* fname, HASHDB_OPENMODE openmode) {
    *db = NULL;
    int ret = 0;

    *db = (hashdb) malloc(sizeof(**db));
    memset(db, 0, sizeof(**db));
    (*db)->h_file = NULL;

    if (*db == NULL) {
        // allocate error
        ret = -2;
        goto err;
    }

    switch(openmode) {
    case HASH_RW:
        (*db)->h_file = fopen(fname, "a+b");
        break;
    case HASH_RO:
        (*db)->h_file = fopen(fname, "rb");
        break;
    case HASH_OW:
        (*db)->h_file = fopen(fname, "w+b");
        break;
    }

    if ((*db)->h_file == NULL) {
        ret = -1;
        goto err;
    }

#ifdef _WIN32
    __int64 size = _filelengthi64(_fileno((*db)->h_file));
    if (size < 0) {
        ret = -3;
        goto err;
    }
    (*db)->size = size;

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
        fclose((*db)->h_file);
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

