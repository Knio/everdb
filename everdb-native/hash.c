#include "hash.h"

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/mman.h>
#endif


void _hash_map_close(hash *db);

int hash_open(hash *db, const char* fname, int readonly, int overwrite) {
    int ret = 0;

    memset(db, 0, sizeof(hash));


    if (readonly && overwrite) {
        ret = -4;
        goto err;
    }
    db->readonly = readonly;

#ifdef _WIN32

    db->h_file = CreateFileA(
        fname,
        readonly ? GENERIC_READ : (GENERIC_READ | GENERIC_WRITE),
        0, NULL,
        overwrite ? CREATE_ALWAYS : OPEN_ALWAYS,
        0, NULL
    );
    if (db->h_file == NULL) {
        ret = -1;
        goto err;
    }

    LARGE_INTEGER f_size;
    if (!GetFileSizeEx(db->h_file, &f_size)) {
        ret = -3;
        goto err;
    }
    db->size = f_size.QuadPart;

    if (db->size & BLOCK_MASK) {
        ret = -5;
        goto err;
    }

    uint64_t size = db->size;

    if (size == 0) {
        size = BLOCK_SIZE;
    }

    _hash_map(db, size);

#else
    //linux here
    ret = -9;
#endif

    if (db->size == 0) {
        // new or overwritten file
        hash_init(db);
    }
    else {
        // existing file
        hash_check(db);
    }

    return ret;

    err:

    hash_close(db);

    if (db != NULL) {
        memset(db, 0, sizeof(hash));
    }
    return ret;
}

void hash_close(hash *db) {
    if (db == NULL) return;

    _hash_map_close(db);
    #ifdef _WIN32
    if (db->h_file != NULL) {
        CloseHandle(db->h_file);
        db->h_file = NULL;
    }
    #endif
}

void _hash_map_close(hash *db) {
    if (db == NULL) return;

    if (db->data != NULL) {
        UnmapViewOfFile(db->data);
        db->data = NULL;
    }

    if (db->h_mapping != NULL) {
        CloseHandle(db->h_mapping);
        db->h_mapping = NULL;
    }
}

int _hash_map(hash *db, uint64_t size) {
    if (db == NULL) return -1;
    int ret = 0;

#ifdef _WIN32

    _hash_map_close(db);

    db->h_mapping = CreateFileMapping(
        db->h_file,
        NULL,
        db->readonly ? PAGE_READONLY : PAGE_READWRITE,
        0, size, NULL
    );

    if (db->h_mapping == NULL) {
        ret = -2;
        goto err;
    }

    db->data = MapViewOfFile(
        db->h_mapping,
        db->readonly ? FILE_MAP_READ : FILE_MAP_ALL_ACCESS,
        0, 0, 0
    );

    if (db->data == NULL) {
        ret = -9;
        goto err;
    }
    db->size = size;

#else
    // linux here
    ret = -9;
#endif

    return ret;

    err:
    _hash_map_close(db);
    db->size = 0;
    return ret;
}

int hash_check(const hash *db) {
    return 0;
}

int hash_init(hash *db) {
    return 0;
}


char* hash_get(const hash *db,
        const char* key, uint32_t nkey) {

    return NULL;
}

int hash_put(hash *db,
        const char* key, uint32_t nkey,
        const char* value, uint32_t nvalue) {

    return 0;
}

