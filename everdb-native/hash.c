#include "hash.h"
#include <malloc.h>

struct hashdb_s {
#ifdef _WIN32
    HANDLE h_file;
    HANDLE h_map;
#else
    void* h_file;
    void* h_map;
#endif
    uint64_t size;
};


hashdb hash_open(const char* fname, int readonly, int overwrite) {
    hashdb db = NULL;

    db = (hashdb) malloc(sizeof(*db));

    if (db == NULL) {
        // allocate error
        goto err;
    }

#ifdef _WIN32
    db->h_file = CreateFileA(fname,
        readonly ? GENERIC_READ : (GENERIC_READ | GENERIC_WRITE),
        0,
        NULL,
        overwrite ? CREATE_ALWAYS : OPEN_ALWAYS,
        0,
        NULL
    );

    if (db->h_file == NULL) {
        // create error
        goto err;
    }

    LARGE_INTEGER f_size;
    if (!GetFileSizeEx(db->h_file, &f_size)) {
        // wat
        goto err;
    }
    db->size = f_size.QuadPart;
#else
    //linux here
#endif
    if (db->size == 0) {
        // new or overwritten file
        hash_init(db);
    }
    else {
        // existing file
        hash_check(db);
    }

    return db;

    err:
    if(db != NULL) {
        free(db);
    }
    return NULL;
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

