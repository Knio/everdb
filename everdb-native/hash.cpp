#include "hash.h"

hash_db* hash_open(
        const char* fname,
        bool readonly,
        bool overwrite) {

    hash_db* db = NULL;

    db = new hash_db;

    if (db == NULL) {
        // allocate error
        goto err;
    }

    #ifdef windows
    db->h_file = CreateFile(fname,
        readonly ? GENERIC_READ : (GENERIC_READ | GENERIC_WRITE),
        0,
        NULL,
        overwrite ? CREATE_ALWAYS : OPEN_ALWAYS,
        0
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
    if (db->size == 0) {
        // new or overwritten file
        hash_init(db);
    }
    else {
        // existing file
        hash_check(db);
    }


    return db;

    #else
    // linux go here
    #endif

    err:
    delete db;
    return NULL;
}


bool hash_check(const hash_db *db) {
    // check header / checksums / etc

    return false;
}

bool hash_init(hash_db *db) {
    // init a new empry db

    return false;
}


char* hash_get(const hash_db* db,
        const char* key, uint32_t nkey) {
    // lookup a key

    return false;
}

int hash_put(
        hash_db* db,
        const char* key, uint32_t nkey,
        const char* value, uint32_t nvalue) {
    // insert/overwrite a key

    return false;
}

