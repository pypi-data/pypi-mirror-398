#define _POSIX_C_SOURCE 200809L
#include "native_dict.h"
#include "uthash.h"
#include <stdlib.h>
#include <string.h>

// Hash table entry structure
struct NativeDictEntry {
    char* key;              // Key (owned by entry)
    void* value;            // Value pointer
    UT_hash_handle hh;      // uthash handle
};

// Dict structure
struct NativeDict {
    NativeDictEntry* entries;  // Hash table head
    size_t size;               // Number of entries
};

// Iterator structure
struct NativeDictIterator {
    NativeDictEntry* current;
    NativeDictEntry* next;
};

// Create a new dict
NativeDict* native_dict_create(void) {
    NativeDict* dict = (NativeDict*)malloc(sizeof(NativeDict));
    if (!dict) return NULL;

    dict->entries = NULL;
    dict->size = 0;
    return dict;
}

// Destroy dict and free all entries
void native_dict_destroy(NativeDict* dict) {
    if (!dict) return;

    NativeDictEntry* entry;
    NativeDictEntry* tmp;

    HASH_ITER(hh, dict->entries, entry, tmp) {
        HASH_DEL(dict->entries, entry);
        free(entry->key);
        free(entry);
    }

    free(dict);
}

// Set a key-value pair
bool native_dict_set(NativeDict* dict, const char* key, void* value) {
    if (!dict || !key) return false;

    NativeDictEntry* entry = NULL;

    // Check if key already exists
    HASH_FIND_STR(dict->entries, key, entry);

    if (entry) {
        // Update existing entry
        entry->value = value;
    } else {
        // Create new entry
        entry = (NativeDictEntry*)malloc(sizeof(NativeDictEntry));
        if (!entry) return false;

        entry->key = strdup(key);
        if (!entry->key) {
            free(entry);
            return false;
        }

        entry->value = value;

        HASH_ADD_KEYPTR(hh, dict->entries, entry->key, strlen(entry->key), entry);
        dict->size++;
    }

    return true;
}

// Get a value by key
void* native_dict_get(NativeDict* dict, const char* key) {
    if (!dict || !key) return NULL;

    NativeDictEntry* entry = NULL;
    HASH_FIND_STR(dict->entries, key, entry);

    return entry ? entry->value : NULL;
}

// Delete a key-value pair
bool native_dict_delete(NativeDict* dict, const char* key) {
    if (!dict || !key) return false;

    NativeDictEntry* entry = NULL;
    HASH_FIND_STR(dict->entries, key, entry);

    if (entry) {
        HASH_DEL(dict->entries, entry);
        free(entry->key);
        free(entry);
        dict->size--;
        return true;
    }

    return false;
}

// Check if key exists
bool native_dict_contains(NativeDict* dict, const char* key) {
    if (!dict || !key) return false;

    NativeDictEntry* entry = NULL;
    HASH_FIND_STR(dict->entries, key, entry);

    return entry != NULL;
}

// Get dict size
size_t native_dict_size(NativeDict* dict) {
    return dict ? dict->size : 0;
}

// Clear all entries
void native_dict_clear(NativeDict* dict) {
    if (!dict) return;

    NativeDictEntry* entry;
    NativeDictEntry* tmp;

    HASH_ITER(hh, dict->entries, entry, tmp) {
        HASH_DEL(dict->entries, entry);
        free(entry->key);
        free(entry);
    }

    dict->entries = NULL;
    dict->size = 0;
}

// Create iterator
NativeDictIterator* native_dict_iter_create(NativeDict* dict) {
    if (!dict) return NULL;

    NativeDictIterator* iter = (NativeDictIterator*)malloc(sizeof(NativeDictIterator));
    if (!iter) return NULL;

    iter->current = NULL;
    iter->next = dict->entries;

    return iter;
}

// Destroy iterator
void native_dict_iter_destroy(NativeDictIterator* iter) {
    free(iter);
}

// Get next key-value pair
bool native_dict_iter_next(NativeDictIterator* iter, const char** key, void** value) {
    if (!iter || !iter->next) return false;

    iter->current = iter->next;
    iter->next = (NativeDictEntry*)(iter->current->hh.next);

    if (key) *key = iter->current->key;
    if (value) *value = iter->current->value;

    return true;
}

// Get all keys
const char** native_dict_keys(NativeDict* dict, size_t* count) {
    if (!dict || !count) return NULL;

    *count = dict->size;
    if (dict->size == 0) return NULL;

    const char** keys = (const char**)malloc(sizeof(char*) * dict->size);
    if (!keys) return NULL;

    NativeDictEntry* entry;
    size_t i = 0;

    for (entry = dict->entries; entry != NULL; entry = (NativeDictEntry*)(entry->hh.next)) {
        keys[i++] = entry->key;
    }

    return keys;
}

// Get all values
void** native_dict_values(NativeDict* dict, size_t* count) {
    if (!dict || !count) return NULL;

    *count = dict->size;
    if (dict->size == 0) return NULL;

    void** values = (void**)malloc(sizeof(void*) * dict->size);
    if (!values) return NULL;

    NativeDictEntry* entry;
    size_t i = 0;

    for (entry = dict->entries; entry != NULL; entry = (NativeDictEntry*)(entry->hh.next)) {
        values[i++] = entry->value;
    }

    return values;
}

// Free keys array
void native_dict_free_keys(const char** keys) {
    free((void*)keys);
}

// Free values array
void native_dict_free_values(void** values) {
    free(values);
}
